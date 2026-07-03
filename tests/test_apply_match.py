"""
test_apply_match.py - Actionable review queue (A1) and audit trail (A2).
Verifies apply_match/reject_match ledger mutation, the shared system/human
path, the double-apply guard, and structured audit entries.
"""

from datetime import date

import pytest

from factoring.mock_data import get_back_office_dataset
from factoring.models import BankPayment, Debtor, Invoice, InvoiceStatus, MatchTier
from factoring.reconciliation_agent import ReconciliationAgent, apply_match, reject_match


def run_demo_feed():
    debtors, invoices, payments = get_back_office_dataset()
    agent = ReconciliationAgent()
    result = agent.process(payments, invoices, debtors)
    by_id = {p.payment_id: p for p in result["results"]}
    return result, by_id, {inv.invoice_id: inv for inv in invoices}


# ---------------------------------------------------------------------------
# A1: apply_match / reject_match ledger mutation
# ---------------------------------------------------------------------------

def test_apply_match_full_payment_marks_paid():
    debtor = {"D001": Debtor("D001", "Acme Corp", "ap@acme.com")}
    inv = Invoice("INV-1", "D001", 10000.0, date(2026, 5, 1), date(2026, 6, 1), "INV-1")
    payment = BankPayment("P1", date(2026, 7, 1), 10000.0, "ACME CORP", "INV-1")
    payment.matched_invoice_ids = ["INV-1"]
    payment.match_confidence = 75
    payment.match_tier = MatchTier.REVIEW
    payment.match_reason = "Partial payment on INV-1: 100% of open amount"

    entry = apply_match(payment, [inv], actor="human")

    assert inv.status == InvoiceStatus.PAID
    assert inv.paid_amount == 10000.0
    assert payment.applied is True
    assert entry["actor"] == "human"
    assert entry["payment_id"] == "P1"
    assert entry["invoice_ids"] == ["INV-1"]


def test_apply_match_short_pay_sets_short_pay_status():
    debtor = {"D001": Debtor("D001", "Acme Corp", "ap@acme.com")}
    inv = Invoice("INV-1", "D001", 10000.0, date(2026, 5, 1), date(2026, 6, 1), "INV-1")
    payment = BankPayment("P1", date(2026, 7, 1), 9800.0, "ACME CORP", "INV-1")
    payment.matched_invoice_ids = ["INV-1"]
    payment.match_confidence = 80
    payment.match_tier = MatchTier.REVIEW
    payment.match_reason = "Short-pay on INV-1: $200.00 under open amount (within 2%)"

    apply_match(payment, [inv], actor="human")

    assert inv.status == InvoiceStatus.SHORT_PAY
    assert inv.paid_amount == 9800.0


def test_apply_match_partial_payment_sets_partial_status():
    debtor = {"D001": Debtor("D001", "Acme Corp", "ap@acme.com")}
    inv = Invoice("INV-1", "D001", 10000.0, date(2026, 5, 1), date(2026, 6, 1), "INV-1")
    payment = BankPayment("P1", date(2026, 7, 1), 4400.0, "ACME CORP", "INV-1")
    payment.matched_invoice_ids = ["INV-1"]
    payment.match_confidence = 75
    payment.match_tier = MatchTier.REVIEW
    payment.match_reason = "Partial payment on INV-1: 44% of open amount"

    apply_match(payment, [inv], actor="human")

    assert inv.status == InvoiceStatus.PARTIAL
    assert inv.paid_amount == 4400.0
    assert inv.open_amount == 5600.0


def test_apply_match_combined_remittance_pays_all_invoices():
    debtor = {"D002": Debtor("D002", "Atlas Building Supply", "payables@atlasbuild.com")}
    inv1 = Invoice("INV-1005", "D002", 7200.00, date(2026, 4, 1), date(2026, 5, 1), "INV-1005")
    inv2 = Invoice("INV-1006", "D002", 9405.75, date(2026, 4, 1), date(2026, 5, 1), "INV-1006")
    inv3 = Invoice("INV-1009", "D002", 6500.00, date(2026, 4, 1), date(2026, 5, 1), "INV-1009")
    payment = BankPayment("P007", date(2026, 7, 1), 23105.75, "ATLAS BUILDING SUPPLY", "AP RUN JUNE")
    payment.matched_invoice_ids = ["INV-1005", "INV-1006", "INV-1009"]
    payment.match_confidence = 78
    payment.match_tier = MatchTier.REVIEW
    payment.match_reason = "Amount equals 3 open invoices"

    invoices = [inv1, inv2, inv3]
    apply_match(payment, invoices, actor="human")

    assert inv1.status == InvoiceStatus.PAID
    assert inv2.status == InvoiceStatus.PAID
    assert inv3.status == InvoiceStatus.PAID
    assert inv1.paid_amount == 7200.00
    assert inv2.paid_amount == 9405.75
    assert inv3.paid_amount == 6500.00


def test_apply_match_double_apply_blocked():
    debtor = {"D001": Debtor("D001", "Acme Corp", "ap@acme.com")}
    inv = Invoice("INV-1", "D001", 10000.0, date(2026, 5, 1), date(2026, 6, 1), "INV-1")
    payment = BankPayment("P1", date(2026, 7, 1), 10000.0, "ACME CORP", "INV-1")
    payment.matched_invoice_ids = ["INV-1"]
    payment.match_confidence = 100
    payment.match_tier = MatchTier.AUTO_APPLY
    payment.match_reason = "Exact reference and amount match"

    apply_match(payment, [inv], actor="system")
    with pytest.raises(ValueError):
        apply_match(payment, [inv], actor="human")

    # Ledger must not double-count
    assert inv.paid_amount == 10000.0


def test_auto_tiers_applied_via_system_actor_share_ledger_path():
    """Auto-applied tiers (100/90) call the same apply_match path as human
    approvals, so system and human actions can never diverge."""
    _, by_id, invoices = run_demo_feed()
    for pid in ("P001", "P002", "P003"):
        assert by_id[pid].applied is True
    assert invoices["INV-1001"].status == InvoiceStatus.PAID


def test_reject_match_routes_to_exception_queue():
    debtor = {"D001": Debtor("D001", "Acme Corp", "ap@acme.com")}
    inv = Invoice("INV-1", "D001", 10000.0, date(2026, 5, 1), date(2026, 6, 1), "INV-1")
    payment = BankPayment("P1", date(2026, 7, 1), 4400.0, "ACME CORP", "INV-1")
    payment.matched_invoice_ids = ["INV-1"]
    payment.match_confidence = 75
    payment.match_tier = MatchTier.REVIEW
    payment.match_reason = "Partial payment on INV-1: 44% of open amount"

    entry = reject_match(payment, reason="needs manual lookup", actor="human")

    assert payment.match_tier == MatchTier.EXCEPTION
    assert payment.applied is False
    assert inv.status == InvoiceStatus.OUTSTANDING  # rejecting does not touch the ledger
    assert entry["actor"] == "human"
    assert entry["reason"] == "needs manual lookup"


def test_reject_match_on_applied_payment_blocked():
    debtor = {"D001": Debtor("D001", "Acme Corp", "ap@acme.com")}
    inv = Invoice("INV-1", "D001", 10000.0, date(2026, 5, 1), date(2026, 6, 1), "INV-1")
    payment = BankPayment("P1", date(2026, 7, 1), 10000.0, "ACME CORP", "INV-1")
    payment.matched_invoice_ids = ["INV-1"]
    payment.match_confidence = 100
    payment.match_tier = MatchTier.AUTO_APPLY
    payment.match_reason = "exact match"
    apply_match(payment, [inv], actor="system")

    with pytest.raises(ValueError):
        reject_match(payment, reason="too late", actor="human")


# ---------------------------------------------------------------------------
# A2: structured, timestamped audit entries
# ---------------------------------------------------------------------------

def test_every_payment_produces_at_least_one_audit_entry():
    result, _, _ = run_demo_feed()
    payment_ids_with_entries = {e["payment_id"] for e in result["audit_trail"]}
    all_payment_ids = {p.payment_id for p in result["results"]}
    assert all_payment_ids.issubset(payment_ids_with_entries)


def test_audit_entry_shape_has_required_keys():
    result, _, _ = run_demo_feed()
    for entry in result["audit_trail"]:
        assert set(entry.keys()) >= {
            "timestamp", "actor", "payment_id", "invoice_ids",
            "tier", "confidence", "reason",
        }
        assert entry["actor"] in ("system", "human")


def test_human_approve_action_is_attributed_in_audit_trail():
    debtor = {"D001": Debtor("D001", "Acme Corp", "ap@acme.com")}
    inv = Invoice("INV-1", "D001", 10000.0, date(2026, 5, 1), date(2026, 6, 1), "INV-1")
    payment = BankPayment("P1", date(2026, 7, 1), 10000.0, "ACME CORP", "INV-1")
    payment.matched_invoice_ids = ["INV-1"]
    payment.match_confidence = 75
    payment.match_tier = MatchTier.REVIEW
    payment.match_reason = "Partial payment on INV-1: 100% of open amount"

    entry = apply_match(payment, [inv], actor="human")

    assert entry["actor"] == "human"
    assert entry["payment_id"] == "P1"
    assert entry["timestamp"] is not None


def test_audit_trail_includes_all_four_tiers():
    result, by_id, _ = run_demo_feed()
    tiers_seen = {e["tier"] for e in result["audit_trail"]}
    # Demo feed exercises AUTO_APPLY, AUTO_APPLY_LOGGED, REVIEW, EXCEPTION
    assert MatchTier.AUTO_APPLY.value in tiers_seen
    assert MatchTier.AUTO_APPLY_LOGGED.value in tiers_seen
    assert MatchTier.REVIEW.value in tiers_seen
    assert MatchTier.EXCEPTION.value in tiers_seen
