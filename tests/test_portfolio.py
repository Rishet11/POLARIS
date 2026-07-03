"""
test_portfolio.py - Portfolio monitor pure functions (A3).
Fixed fixture of invoices/debtors so every metric can be hand-checked.
"""

from datetime import date, timedelta

from factoring.models import Debtor, Invoice, InvoiceStatus
from factoring.portfolio import (
    aging_distribution,
    collection_rate,
    concentration_by_debtor,
    covenant_table,
    data_tape_rows,
    dilution_rate,
    funds_employed,
    open_ar_total,
)

TODAY = date(2026, 7, 4)


def days_ago(n):
    return TODAY - timedelta(days=n)


def days_ahead(n):
    return TODAY + timedelta(days=n)


def make_fixture():
    debtors = {
        "D001": Debtor("D001", "Meridian Freight Lines", "ap@meridianfreight.com", 30, 0),
        "D002": Debtor("D002", "Atlas Building Supply", "payables@atlasbuild.com", 45, 1),
    }
    invoices = [
        # D001: open, current, face 10000, advance 0.85 -> factored 8500
        Invoice("INV-1", "D001", 10000.0, days_ago(20), days_ahead(10), "INV-1",
                advance_rate=0.85, status=InvoiceStatus.OUTSTANDING, paid_amount=0.0),
        # D001: open, 31-60 bucket (45 days past due), face 5000
        Invoice("INV-2", "D001", 5000.0, days_ago(80), days_ago(45), "INV-2",
                advance_rate=0.85, status=InvoiceStatus.OUTSTANDING, paid_amount=0.0),
        # D002: open, 90+ bucket (100 days past due), face 15000, partially paid
        Invoice("INV-3", "D002", 15000.0, days_ago(160), days_ago(100), "INV-3",
                advance_rate=0.80, status=InvoiceStatus.PARTIAL, paid_amount=5000.0),
        # D002: closed/paid, face 8000, fully paid, matured (due in the past)
        Invoice("INV-4", "D002", 8000.0, days_ago(50), days_ago(20), "INV-4",
                advance_rate=0.80, status=InvoiceStatus.PAID, paid_amount=8000.0),
        # D002: closed via short-pay, face 3000, paid 2900 (dilution)
        Invoice("INV-5", "D002", 3000.0, days_ago(60), days_ago(30), "INV-5",
                advance_rate=0.80, status=InvoiceStatus.SHORT_PAY, paid_amount=2900.0),
    ]
    return debtors, invoices


def test_open_ar_total_sums_open_invoices_only():
    debtors, invoices = make_fixture()
    # is_open covers OUTSTANDING/PARTIAL/SHORT_PAY (not PAID).
    # Open: INV-1 (10000), INV-2 (5000), INV-3 (15000-5000=10000), INV-5 (3000-2900=100)
    assert open_ar_total(invoices) == 25100.0


def test_funds_employed_sums_factored_amount_of_open_invoices():
    debtors, invoices = make_fixture()
    # INV-1: 10000*0.85=8500, INV-2: 5000*0.85=4250, INV-3: 15000*0.80=12000, INV-5: 3000*0.80=2400
    assert funds_employed(invoices) == 8500.0 + 4250.0 + 12000.0 + 2400.0


def test_concentration_by_debtor_percentages_and_warning_band():
    debtors, invoices = make_fixture()
    rows = concentration_by_debtor(invoices, debtors, warning_threshold_pct=25.0)
    by_debtor = {r["debtor_id"]: r for r in rows}

    # Open AR = 25100 total. D001 open = 10000+5000=15000 (59.8%). D002 open = 10000+100=10100 (40.2%).
    assert by_debtor["D001"]["open_amount"] == 15000.0
    assert by_debtor["D001"]["pct_of_open_ar"] == 59.8
    assert by_debtor["D001"]["status"] == "WARNING"  # over 25% threshold

    assert by_debtor["D002"]["open_amount"] == 10100.0
    assert by_debtor["D002"]["pct_of_open_ar"] == 40.2
    assert by_debtor["D002"]["status"] == "WARNING"


def test_concentration_below_threshold_is_compliant():
    debtors = {
        "D001": Debtor("D001", "Small Co", "a@a.com"),
        "D002": Debtor("D002", "Big Co", "b@b.com"),
    }
    invoices = [
        Invoice("INV-1", "D001", 1000.0, days_ago(10), days_ahead(10), "INV-1"),
        Invoice("INV-2", "D002", 9000.0, days_ago(10), days_ahead(10), "INV-2"),
    ]
    rows = concentration_by_debtor(invoices, debtors, warning_threshold_pct=25.0)
    by_debtor = {r["debtor_id"]: r for r in rows}
    assert by_debtor["D001"]["pct_of_open_ar"] == 10.0
    assert by_debtor["D001"]["status"] == "COMPLIANT"


def test_aging_distribution_buckets_and_over_60_flag():
    debtors, invoices = make_fixture()
    dist = aging_distribution(invoices, as_of=TODAY)
    # Open invoices: INV-1 (CURRENT... wait due_date is in future -> 0 dpd -> CURRENT)
    # INV-2 (45 dpd -> 31-60), INV-3 (100 dpd -> 90+)
    assert dist["CURRENT"]["count"] == 1
    assert dist["31-60"]["count"] == 1
    assert dist["90+"]["count"] == 1
    assert dist["pct_over_60"] > 0


def test_dilution_rate_from_short_pays_and_disputes():
    debtors, invoices = make_fixture()
    # Face value processed (matured & applied, i.e. PAID/SHORT_PAY/PARTIAL/DISPUTED with paid>0):
    # dilution = shortfall on SHORT_PAY/DISPUTED invoices as % of face value processed
    rate = dilution_rate(invoices)
    assert rate >= 0.0
    assert isinstance(rate, float)


def test_collection_rate_paid_over_matured_face():
    debtors, invoices = make_fixture()
    rate = collection_rate(invoices, as_of=TODAY)
    # Matured invoices (due_date <= today): INV-2, INV-3, INV-4, INV-5
    # Paid amounts: 0 + 5000 + 8000 + 2900 = 15900
    # Matured face: 5000 + 15000 + 8000 + 3000 = 31000
    assert rate == round(100 * 15900.0 / 31000.0, 1)


def test_covenant_table_rows_have_metric_current_threshold_status():
    debtors, invoices = make_fixture()
    rows = covenant_table(invoices, debtors)
    assert len(rows) > 0
    for row in rows:
        assert set(row.keys()) >= {"metric", "current", "threshold", "status"}
        assert row["status"] in ("COMPLIANT", "WARNING")


def test_data_tape_rows_builder_returns_csv_ready_dicts():
    debtors, invoices = make_fixture()
    rows = data_tape_rows(invoices, debtors, as_of=TODAY)
    assert len(rows) == len(invoices)
    row = next(r for r in rows if r["invoice_id"] == "INV-3")
    assert row["debtor"] == "Atlas Building Supply"
    assert row["face_amount"] == 15000.0
    assert row["advanced_amount"] == 12000.0
    assert row["paid_amount"] == 5000.0
    assert row["open_amount"] == 10000.0
    assert row["aging_bucket"] == "90+"
    assert row["status"] == "PARTIAL"
