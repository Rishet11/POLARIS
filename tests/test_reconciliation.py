"""
test_reconciliation.py - Cash application engine tests.
Verifies every confidence tier against the demo bank feed plus edge cases.
"""

from datetime import date

from factoring.mock_data import get_back_office_dataset
from factoring.models import BankPayment, Debtor, Invoice, InvoiceStatus, MatchTier
from factoring.reconciliation_agent import ReconciliationAgent


def run_demo_feed():
    debtors, invoices, payments = get_back_office_dataset()
    agent = ReconciliationAgent()
    result = agent.process(payments, invoices, debtors)
    by_id = {p.payment_id: p for p in result["results"]}
    return result, by_id, {inv.invoice_id: inv for inv in invoices}


def test_exact_ref_and_amount_auto_applies():
    _, by_id, invoices = run_demo_feed()
    for pid, inv_id in [("P001", "INV-1001"), ("P002", "INV-1003"), ("P003", "INV-1007")]:
        assert by_id[pid].match_tier == MatchTier.AUTO_APPLY
        assert by_id[pid].match_confidence == 100
        assert by_id[pid].matched_invoice_ids == [inv_id]
        assert invoices[inv_id].status == InvoiceStatus.PAID


def test_unique_amount_without_ref_auto_applies_with_log():
    result, by_id, invoices = run_demo_feed()
    assert by_id["P004"].match_tier == MatchTier.AUTO_APPLY_LOGGED
    assert by_id["P004"].matched_invoice_ids == ["INV-1004"]
    assert by_id["P005"].match_tier == MatchTier.AUTO_APPLY_LOGGED
    assert by_id["P005"].matched_invoice_ids == ["INV-1008"]
    assert invoices["INV-1004"].status == InvoiceStatus.PAID
    # Both auto-logged applications appear in the audit log
    assert len(result["audit_log"]) == 2


def test_short_pay_within_tolerance_goes_to_review():
    _, by_id, invoices = run_demo_feed()
    p = by_id["P006"]
    assert p.match_tier == MatchTier.REVIEW
    assert p.matched_invoice_ids == ["INV-1002"]
    assert "Short-pay" in p.match_reason
    # Review tier is NOT auto-applied — invoice stays open for a human
    assert invoices["INV-1002"].status == InvoiceStatus.OUTSTANDING


def test_combined_remittance_matches_multiple_invoices():
    _, by_id, _ = run_demo_feed()
    p = by_id["P007"]
    assert p.match_tier == MatchTier.REVIEW
    assert sorted(p.matched_invoice_ids) == ["INV-1005", "INV-1006", "INV-1009"]


def test_partial_payment_goes_to_review():
    _, by_id, invoices = run_demo_feed()
    p = by_id["P008"]
    assert p.match_tier == MatchTier.REVIEW
    assert p.matched_invoice_ids == ["INV-1010"]
    assert "Partial" in p.match_reason
    assert invoices["INV-1010"].status == InvoiceStatus.OUTSTANDING


def test_reused_reference_routes_to_exception():
    _, by_id, _ = run_demo_feed()
    p = by_id["P009"]
    assert p.match_tier == MatchTier.EXCEPTION
    assert sorted(p.matched_invoice_ids) == ["INV-1011", "INV-1012"]


def test_ambiguous_amount_routes_to_exception():
    _, by_id, _ = run_demo_feed()
    p = by_id["P010"]
    assert p.match_tier == MatchTier.EXCEPTION
    assert sorted(p.matched_invoice_ids) == ["INV-1013", "INV-1014"]


def test_kpis_aggregate_correctly():
    result, _, _ = run_demo_feed()
    kpis = result["kpis"]
    assert kpis["total_payments"] == 10
    assert kpis["auto_applied"] == 5
    assert kpis["auto_match_rate"] == 50.0
    assert kpis["review"] == 3
    assert kpis["exceptions"] == 2


def test_short_pay_tolerance_boundary():
    """Exactly at 2% under → REVIEW short-pay; beyond 2% → partial payment."""
    debtor = {"D001": Debtor("D001", "Acme Corp", "ap@acme.com")}
    agent = ReconciliationAgent()

    inv = Invoice("INV-1", "D001", 10000.0, date(2026, 5, 1), date(2026, 6, 1), "INV-1")
    at_boundary = BankPayment("P1", date(2026, 7, 1), 9800.0, "ACME CORP", "INV-1")
    agent.process([at_boundary], [inv], debtor)
    assert at_boundary.match_tier == MatchTier.REVIEW
    assert "Short-pay" in at_boundary.match_reason

    inv2 = Invoice("INV-2", "D001", 10000.0, date(2026, 5, 1), date(2026, 6, 1), "INV-2")
    beyond = BankPayment("P2", date(2026, 7, 1), 9799.0, "ACME CORP", "INV-2")
    agent.process([beyond], [inv2], debtor)
    assert beyond.match_tier == MatchTier.REVIEW
    assert "Partial" in beyond.match_reason


def test_overpayment_routes_to_exception():
    debtor = {"D001": Debtor("D001", "Acme Corp", "ap@acme.com")}
    inv = Invoice("INV-1", "D001", 10000.0, date(2026, 5, 1), date(2026, 6, 1), "INV-1")
    p = BankPayment("P1", date(2026, 7, 1), 12000.0, "ACME CORP", "INV-1")
    ReconciliationAgent().process([p], [inv], debtor)
    assert p.match_tier == MatchTier.EXCEPTION
    assert "exceeds" in p.match_reason


def test_paid_invoices_leave_matching_pool():
    """A second identical payment cannot re-match an already-paid invoice."""
    debtor = {"D001": Debtor("D001", "Acme Corp", "ap@acme.com")}
    inv = Invoice("INV-1", "D001", 5000.0, date(2026, 5, 1), date(2026, 6, 1), "INV-1")
    first = BankPayment("P1", date(2026, 7, 1), 5000.0, "ACME CORP", "INV-1")
    duplicate = BankPayment("P2", date(2026, 7, 2), 5000.0, "ACME CORP", "INV-1")
    ReconciliationAgent().process([first, duplicate], [inv], debtor)
    assert first.match_tier == MatchTier.AUTO_APPLY
    assert duplicate.match_tier == MatchTier.EXCEPTION
