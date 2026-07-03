"""
POLARIS Reconciliation Agent (Cash Application)
Matches incoming bank payments to open factored invoices with
confidence-tiered results. Pure rules, no LLM: in cash application,
a wrong automatic match moves real money to the wrong ledger.

Tiers:
  100        AUTO_APPLY         exact reference + exact open amount
  90         AUTO_APPLY_LOGGED  unambiguous amount match, applied with audit log
  70-89      REVIEW             probable match (short-pay, combined, partial)
  <70        EXCEPTION          ambiguous or no signal — human queue
"""

import itertools
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from .models import BankPayment, Debtor, Invoice, InvoiceStatus, MatchTier

# Tolerance for short-pays (wire fees, small deductions): 2% of open amount
SHORT_PAY_TOLERANCE = 0.02

# Reference tokens we recognize in wire/ACH memo text
REF_PATTERN = re.compile(r"\b(?:INV|PO)-\d+\b", re.IGNORECASE)

# Max invoices considered in a combined-remittance match
MAX_COMBO_SIZE = 4


def _audit_entry(payment: BankPayment, actor: str, reason: Optional[str] = None) -> Dict[str, Any]:
    """Build a structured, timestamped audit entry for one decision or action."""
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "actor": actor,
        "payment_id": payment.payment_id,
        "invoice_ids": list(payment.matched_invoice_ids),
        "tier": payment.match_tier.value if payment.match_tier else None,
        "confidence": payment.match_confidence,
        "reason": reason if reason is not None else payment.match_reason,
    }


def apply_match(
    payment: BankPayment,
    invoices: List[Invoice],
    actor: str = "human",
) -> Dict[str, Any]:
    """
    Apply a matched payment to the ledger: mutate invoice paid_amount/status
    and mark the payment as applied. Used by BOTH the auto-tier path
    (actor="system") and human review-queue approvals (actor="human"), so
    ledger state is identical regardless of who approved the match.

    Guarded: a payment can never be applied twice.
    """
    if payment.applied:
        raise ValueError(f"{payment.payment_id} is already applied — cannot double-apply")
    if not payment.matched_invoice_ids:
        raise ValueError(f"{payment.payment_id} has no matched invoices to apply")

    by_id = {inv.invoice_id: inv for inv in invoices}
    remaining = payment.amount

    for invoice_id in payment.matched_invoice_ids:
        inv = by_id[invoice_id]
        allocation = min(remaining, inv.open_amount)
        inv.paid_amount = round(inv.paid_amount + allocation, 2)
        remaining = round(remaining - allocation, 2)

        if inv.open_amount <= 0.005:
            inv.status = InvoiceStatus.PAID
        elif inv.paid_amount <= 0:
            pass  # nothing allocated to this invoice; leave status untouched
        else:
            is_short_pay = (
                payment.match_reason is not None and "short-pay" in payment.match_reason.lower()
            )
            inv.status = InvoiceStatus.SHORT_PAY if is_short_pay else InvoiceStatus.PARTIAL

    payment.applied = True
    return _audit_entry(payment, actor)


def reject_match(
    payment: BankPayment,
    reason: str,
    actor: str = "human",
) -> Dict[str, Any]:
    """
    Reject a suggested match and route the payment to the exception queue.
    Does not touch ledger state. Guarded: cannot reject an already-applied
    payment.
    """
    if payment.applied:
        raise ValueError(f"{payment.payment_id} is already applied — cannot reject")

    payment.match_tier = MatchTier.EXCEPTION
    payment.match_reason = reason
    return _audit_entry(payment, actor, reason=reason)


class ReconciliationAgent:
    """Deterministic cash-application engine with confidence tiers."""

    name = "RECONCILIATION_AGENT"

    def process(
        self,
        payments: List[BankPayment],
        invoices: List[Invoice],
        debtors: Dict[str, Debtor],
    ) -> Dict[str, Any]:
        """
        Run cash application over the bank feed.

        Payments are processed in order. AUTO_APPLY and AUTO_APPLY_LOGGED
        matches are applied immediately (invoice status/paid_amount updated);
        REVIEW and EXCEPTION results only carry suggested matches and wait
        for a human.

        Returns {results, kpis, audit_log, audit_trail}. `audit_log` (plain
        strings) is kept for backward compatibility; `audit_trail` (A2) is a
        structured, timestamped entry for every payment's decision, across
        all four tiers, plus any later human approve/reject action.
        """
        audit_log: List[str] = []
        audit_trail: List[Dict[str, Any]] = []

        for payment in payments:
            self._match_payment(payment, invoices, debtors)
            if payment.match_tier in (MatchTier.AUTO_APPLY, MatchTier.AUTO_APPLY_LOGGED):
                entry = apply_match(payment, invoices, actor="system")
                audit_trail.append(entry)
                if payment.match_tier == MatchTier.AUTO_APPLY_LOGGED:
                    audit_log.append(
                        f"{payment.payment_id}: auto-applied at {payment.match_confidence}% "
                        f"to {', '.join(payment.matched_invoice_ids)} — {payment.match_reason}"
                    )
            else:
                # REVIEW / EXCEPTION: not applied yet, but the decision itself
                # (what tier, why) is still timestamped and searchable.
                audit_trail.append(_audit_entry(payment, actor="system"))

        tiers = [p.match_tier for p in payments]
        auto = sum(1 for t in tiers if t in (MatchTier.AUTO_APPLY, MatchTier.AUTO_APPLY_LOGGED))
        review = sum(1 for t in tiers if t == MatchTier.REVIEW)
        exceptions = sum(1 for t in tiers if t == MatchTier.EXCEPTION)

        return {
            "results": payments,
            "kpis": {
                "total_payments": len(payments),
                "auto_applied": auto,
                "auto_match_rate": round(100 * auto / len(payments), 1) if payments else 0.0,
                "review": review,
                "exceptions": exceptions,
            },
            "audit_log": audit_log,
            "audit_trail": audit_trail,
        }

    # ------------------------------------------------------------------
    # Matching
    # ------------------------------------------------------------------

    def _match_payment(
        self,
        payment: BankPayment,
        invoices: List[Invoice],
        debtors: Dict[str, Debtor],
    ) -> None:
        open_invoices = [inv for inv in invoices if inv.is_open]

        # Step 1: reference tokens in the memo text
        refs = {r.upper() for r in REF_PATTERN.findall(payment.reference_text or "")}
        ref_matches = [inv for inv in open_invoices if inv.reference_no.upper() in refs]

        if len(ref_matches) == 1:
            self._score_single_ref_match(payment, ref_matches[0])
            return

        if len(ref_matches) > 1:
            # Reference is ambiguous (e.g. client reused a PO number).
            exact = [inv for inv in ref_matches if self._amounts_equal(payment.amount, inv.open_amount)]
            if len(exact) == 1:
                self._set(payment, [exact[0].invoice_id], 85, MatchTier.REVIEW,
                          f"Reference matches {len(ref_matches)} invoices; amount matches "
                          f"only {exact[0].invoice_id}")
            else:
                self._set(payment, [inv.invoice_id for inv in ref_matches], 50, MatchTier.EXCEPTION,
                          f"Reference matches {len(ref_matches)} invoices "
                          f"({', '.join(inv.invoice_id for inv in ref_matches)}) and amount "
                          "matches none — cannot attribute")
            return

        # Step 2: no usable reference — try exact amount
        amount_matches = [
            inv for inv in open_invoices
            if self._amounts_equal(payment.amount, inv.open_amount)
        ]
        if len(amount_matches) == 1:
            self._set(payment, [amount_matches[0].invoice_id], 90, MatchTier.AUTO_APPLY_LOGGED,
                      f"No usable reference, but amount ${payment.amount:,.2f} uniquely "
                      f"matches {amount_matches[0].invoice_id}")
            return
        if len(amount_matches) > 1:
            self._set(payment, [inv.invoice_id for inv in amount_matches], 45, MatchTier.EXCEPTION,
                      f"No reference and ${payment.amount:,.2f} matches "
                      f"{len(amount_matches)} open invoices — cannot attribute")
            return

        # Step 3: combined remittance — subset of one debtor's open invoices
        combo = self._find_combo(payment, open_invoices, debtors)
        if combo:
            self._set(payment, [inv.invoice_id for inv in combo], 78, MatchTier.REVIEW,
                      f"Amount equals {len(combo)} open invoices from "
                      f"{debtors[combo[0].debtor_id].name} "
                      f"({' + '.join(inv.invoice_id for inv in combo)})")
            return

        # Step 4: nothing usable
        self._set(payment, [], 40, MatchTier.EXCEPTION,
                  "No reference, no amount match, no combination match")

    def _score_single_ref_match(self, payment: BankPayment, inv: Invoice) -> None:
        open_amt = inv.open_amount
        if self._amounts_equal(payment.amount, open_amt):
            self._set(payment, [inv.invoice_id], 100, MatchTier.AUTO_APPLY,
                      f"Exact reference and amount match on {inv.invoice_id}")
        elif open_amt * (1 - SHORT_PAY_TOLERANCE) <= payment.amount < open_amt:
            shortfall = open_amt - payment.amount
            self._set(payment, [inv.invoice_id], 80, MatchTier.REVIEW,
                      f"Short-pay on {inv.invoice_id}: ${shortfall:,.2f} under open amount "
                      "(within 2% — likely wire fee or deduction)")
        elif payment.amount < open_amt:
            pct = 100 * payment.amount / open_amt
            self._set(payment, [inv.invoice_id], 75, MatchTier.REVIEW,
                      f"Partial payment on {inv.invoice_id}: {pct:.0f}% of open amount")
        else:
            self._set(payment, [inv.invoice_id], 60, MatchTier.EXCEPTION,
                      f"Payment exceeds open amount on {inv.invoice_id} — possible "
                      "overpayment or misdirected funds")

    def _find_combo(
        self,
        payment: BankPayment,
        open_invoices: List[Invoice],
        debtors: Dict[str, Debtor],
    ) -> Optional[List[Invoice]]:
        debtor_id = self._resolve_debtor(payment.payer_name, debtors)
        if not debtor_id:
            return None
        candidates = [inv for inv in open_invoices if inv.debtor_id == debtor_id]
        for size in range(2, min(MAX_COMBO_SIZE, len(candidates)) + 1):
            for combo in itertools.combinations(candidates, size):
                if self._amounts_equal(sum(inv.open_amount for inv in combo), payment.amount):
                    return list(combo)
        return None

    @staticmethod
    def _resolve_debtor(payer_name: str, debtors: Dict[str, Debtor]) -> Optional[str]:
        """Fuzzy payer-name → debtor mapping via token overlap."""
        payer_tokens = set(re.findall(r"[A-Z]+", payer_name.upper()))
        best_id, best_overlap = None, 0
        for debtor_id, debtor in debtors.items():
            name_tokens = set(re.findall(r"[A-Z]+", debtor.name.upper()))
            overlap = len(payer_tokens & name_tokens)
            if overlap > best_overlap:
                best_id, best_overlap = debtor_id, overlap
        return best_id if best_overlap >= 1 else None

    @staticmethod
    def _amounts_equal(a: float, b: float) -> bool:
        return abs(a - b) < 0.005

    @staticmethod
    def _set(payment: BankPayment, invoice_ids: List[str], confidence: int,
             tier: MatchTier, reason: str) -> None:
        payment.matched_invoice_ids = invoice_ids
        payment.match_confidence = confidence
        payment.match_tier = tier
        payment.match_reason = reason
