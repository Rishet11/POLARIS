"""
POLARIS Collections Agent
Prioritizes past-due factored invoices and drives each case through the
collections FSM. The LLM only drafts message wording; every decision
about WHO to contact, WHEN, and WHAT HAPPENS NEXT is deterministic and
guarded by the FSM (collections_fsm.py).
"""

from datetime import date
from typing import Dict, List, Optional, Tuple

from config import DEMO_MODE, get_model
from .collections_fsm import CollectionCase, CollectionOutcome, CollectionStage
from .models import AgingBucket, Debtor, Invoice

# Aging-bucket priority weights: older debt is exponentially more urgent
BUCKET_WEIGHTS = {
    AgingBucket.DAYS_1_30: 1.0,
    AgingBucket.DAYS_31_60: 1.5,
    AgingBucket.DAYS_61_90: 2.0,
    AgingBucket.DAYS_90_PLUS: 3.0,
}

PROMISE_KEYWORDS = ("will pay", "promise", "by friday", "next week", "processing payment",
                    "check is", "scheduled")
DISPUTE_KEYWORDS = ("dispute", "wrong", "never received", "not ours", "incorrect",
                    "damaged", "returned", "credit memo")


class CollectionsAgent:
    """Rule-driven collections orchestrator with LLM-drafted wording."""

    name = "COLLECTIONS_AGENT"

    def __init__(self):
        self.model = None if DEMO_MODE else get_model()

    # ------------------------------------------------------------------
    # Prioritization
    # ------------------------------------------------------------------

    def prioritize(
        self,
        invoices: List[Invoice],
        debtors: Dict[str, Debtor],
        as_of: Optional[date] = None,
    ) -> List[CollectionCase]:
        """
        Build the collections queue: one case per open, past-due invoice,
        ranked by priority = factored amount × aging weight × (1 + dispute history).
        """
        cases = []
        for inv in invoices:
            if not inv.is_open or inv.days_past_due(as_of) == 0:
                continue
            bucket = inv.aging_bucket(as_of)
            debtor = debtors[inv.debtor_id]
            score = (
                inv.factored_amount
                * BUCKET_WEIGHTS[bucket]
                * (1 + debtor.dispute_history_count)
            )
            cases.append(CollectionCase(
                case_id=f"CASE-{inv.invoice_id}",
                invoice_id=inv.invoice_id,
                debtor_id=inv.debtor_id,
                open_amount=inv.open_amount,
                factored_amount=inv.factored_amount,
                aging_bucket=bucket.value,
                priority_score=score,
            ))
        cases.sort(key=lambda c: c.priority_score, reverse=True)
        return cases

    # ------------------------------------------------------------------
    # Outreach
    # ------------------------------------------------------------------

    def draft_reminder(self, case: CollectionCase, invoice: Invoice, debtor: Debtor) -> str:
        """Draft the next dunning message. Template in demo mode, LLM otherwise."""
        attempt = case.outreach_count + 1
        template = self._template(case, invoice, debtor, attempt)
        if self.model is None:
            return template
        try:
            prompt = (
                "Rewrite this accounts-receivable payment reminder so it is professional, "
                "firm, and under 90 words. Keep every number and date exactly as given. "
                f"Do not invent facts.\n\n{template}"
            )
            return self.model.generate_content(prompt).text.strip()
        except Exception:
            return template  # never let a drafting failure stall a case

    @staticmethod
    def _template(case: CollectionCase, invoice: Invoice, debtor: Debtor, attempt: int) -> str:
        dpd = invoice.days_past_due()
        if attempt == 1:
            return (
                f"Dear {debtor.name} accounts payable,\n\n"
                f"Our records show invoice {invoice.invoice_id} for "
                f"${invoice.open_amount:,.2f} was due on {invoice.due_date.isoformat()} "
                f"and is now {dpd} days past due. Please confirm the payment date, or let "
                f"us know if there is an issue with this invoice.\n\n"
                f"Regards,\nPOLARIS Receivables"
            )
        return (
            f"Dear {debtor.name} accounts payable,\n\n"
            f"Second notice: invoice {invoice.invoice_id} "
            f"(${invoice.open_amount:,.2f}, {dpd} days past due) remains unpaid and we "
            f"have not received a response to our previous reminder. Please remit payment "
            f"or reply with a payment date within 3 business days to avoid escalation.\n\n"
            f"Regards,\nPOLARIS Receivables"
        )

    def run_outreach(
        self, case: CollectionCase, invoice: Invoice, debtor: Debtor
    ) -> Tuple[CollectionOutcome, Optional[str]]:
        """One full outreach step: enter OUTREACH, draft, send (guarded)."""
        # A previously blocked send can leave the case sitting in OUTREACH;
        # re-entering it would be an illegal self-transition.
        if case.stage is not CollectionStage.OUTREACH:
            outcome = case.start_outreach()
            if outcome is not CollectionOutcome.OK:
                return outcome, None
        message = self.draft_reminder(case, invoice, debtor)
        outcome, sent = case.send_message(message)
        if outcome is CollectionOutcome.BLOCKED_DUPLICATE_MESSAGE:
            # LLM produced wording identical to an earlier send. The raw
            # template is distinct per attempt, so retry with it; if even
            # that is a duplicate, this really is a repeated step — stay blocked.
            fallback = self._template(case, invoice, debtor, case.outreach_count + 1)
            if fallback != message:
                return case.send_message(fallback)
        return outcome, sent

    # ------------------------------------------------------------------
    # Response handling
    # ------------------------------------------------------------------

    @staticmethod
    def classify_response(text: str) -> str:
        """Classify a debtor reply: PROMISE, DISPUTE, or UNCLEAR."""
        lowered = text.lower()
        if any(k in lowered for k in DISPUTE_KEYWORDS):
            return "DISPUTE"
        if any(k in lowered for k in PROMISE_KEYWORDS):
            return "PROMISE"
        return "UNCLEAR"

    def handle_response(
        self, case: CollectionCase, text: str, promise_date: Optional[date] = None
    ) -> CollectionOutcome:
        """Route a debtor reply through the FSM."""
        kind = self.classify_response(text)
        if kind == "DISPUTE":
            return case.record_dispute(text.strip()[:120])
        if kind == "PROMISE":
            return case.record_promise(promise_date or date.today())
        # Unclear reply: stay in AWAIT_RESPONSE; caller decides next outreach/escalation
        case.history.append(f"UNCLEAR response recorded: {text.strip()[:80]}")
        return CollectionOutcome.OK
