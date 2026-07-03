"""
POLARIS Portfolio Monitor
Pure functions over the existing Invoice/Debtor models: concentration,
aging distribution, dilution, collection rate, and a covenant-style
threshold table. No state, no side effects, no LLM.
"""

from datetime import date
from typing import Any, Dict, List, Optional

from .models import AgingBucket, Debtor, Invoice, InvoiceStatus

# Configurable sample policy thresholds (not a published industry number —
# a demo default that can be tuned per portfolio).
DEFAULT_CONCENTRATION_WARNING_PCT = 25.0
DEFAULT_AGING_OVER_60_WARNING_PCT = 20.0
DEFAULT_DILUTION_WARNING_PCT = 3.0
DEFAULT_COLLECTION_RATE_WARNING_PCT = 85.0

# Statuses whose paid_amount reflects money actually collected from the debtor,
# i.e. the invoice has matured and something has been applied against it.
_DILUTION_ELIGIBLE_STATUSES = (InvoiceStatus.SHORT_PAY, InvoiceStatus.DISPUTED)


def open_ar_total(invoices: List[Invoice]) -> float:
    """Sum of open_amount across all open invoices."""
    return round(sum(inv.open_amount for inv in invoices if inv.is_open), 2)


def funds_employed(invoices: List[Invoice]) -> float:
    """Sum of factored_amount (capital advanced) across all open invoices."""
    return round(sum(inv.factored_amount for inv in invoices if inv.is_open), 2)


def concentration_by_debtor(
    invoices: List[Invoice],
    debtors: Dict[str, Debtor],
    warning_threshold_pct: float = DEFAULT_CONCENTRATION_WARNING_PCT,
) -> List[Dict[str, Any]]:
    """
    Open AR concentration per account debtor, as % of total open AR, flagged
    when a single debtor exceeds warning_threshold_pct (configurable sample
    policy — no published threshold is assumed here).
    """
    total_open = open_ar_total(invoices)
    by_debtor: Dict[str, float] = {}
    for inv in invoices:
        if not inv.is_open:
            continue
        by_debtor[inv.debtor_id] = by_debtor.get(inv.debtor_id, 0.0) + inv.open_amount

    rows = []
    for debtor_id, open_amount in by_debtor.items():
        pct = round(100 * open_amount / total_open, 1) if total_open else 0.0
        rows.append({
            "debtor_id": debtor_id,
            "debtor_name": debtors[debtor_id].name if debtor_id in debtors else debtor_id,
            "open_amount": round(open_amount, 2),
            "pct_of_open_ar": pct,
            "status": "WARNING" if pct >= warning_threshold_pct else "COMPLIANT",
        })
    rows.sort(key=lambda r: r["pct_of_open_ar"], reverse=True)
    return rows


def aging_distribution(
    invoices: List[Invoice],
    as_of: Optional[date] = None,
    over_60_warning_pct: float = DEFAULT_AGING_OVER_60_WARNING_PCT,
) -> Dict[str, Any]:
    """
    Distribution of open invoices across aging buckets, by count and by
    open dollar amount, plus the % of open AR that is over 60 days past due.
    """
    open_invoices = [inv for inv in invoices if inv.is_open]
    total_open = sum(inv.open_amount for inv in open_invoices)

    buckets = {b.value: {"count": 0, "amount": 0.0} for b in AgingBucket}
    for inv in open_invoices:
        bucket = inv.aging_bucket(as_of).value
        buckets[bucket]["count"] += 1
        buckets[bucket]["amount"] += inv.open_amount

    over_60_amount = buckets[AgingBucket.DAYS_61_90.value]["amount"] + \
        buckets[AgingBucket.DAYS_90_PLUS.value]["amount"]
    pct_over_60 = round(100 * over_60_amount / total_open, 1) if total_open else 0.0

    result: Dict[str, Any] = {}
    for bucket_name, data in buckets.items():
        pct = round(100 * data["amount"] / total_open, 1) if total_open else 0.0
        result[bucket_name] = {
            "count": data["count"],
            "amount": round(data["amount"], 2),
            "pct_of_open_ar": pct,
        }
    result["pct_over_60"] = pct_over_60
    result["status"] = "WARNING" if pct_over_60 >= over_60_warning_pct else "COMPLIANT"
    return result


def dilution_rate(
    invoices: List[Invoice],
    warning_threshold_pct: float = DEFAULT_DILUTION_WARNING_PCT,
) -> float:
    """
    Dilution proxy: short-pays + disputes (the face-value shortfall on
    invoices in those statuses) as a % of total face value processed
    (all invoices with any paid_amount recorded, open or closed).
    """
    processed = [inv for inv in invoices if inv.paid_amount > 0 or inv.status in _DILUTION_ELIGIBLE_STATUSES]
    face_value_processed = sum(inv.face_amount for inv in processed)
    if not face_value_processed:
        return 0.0

    shortfall = sum(
        inv.face_amount - inv.paid_amount
        for inv in invoices
        if inv.status in _DILUTION_ELIGIBLE_STATUSES
    )
    return round(100 * shortfall / face_value_processed, 2)


def collection_rate(invoices: List[Invoice], as_of: Optional[date] = None) -> float:
    """
    Paid amount / matured face amount, as a %. "Matured" = due_date has
    passed as of `as_of` (defaults to today) — the invoices we'd expect
    payment on by now, regardless of current status.
    """
    as_of = as_of or date.today()
    matured = [inv for inv in invoices if inv.due_date <= as_of]
    matured_face = sum(inv.face_amount for inv in matured)
    if not matured_face:
        return 0.0
    paid = sum(inv.paid_amount for inv in matured)
    return round(100 * paid / matured_face, 1)


def covenant_table(
    invoices: List[Invoice],
    debtors: Dict[str, Debtor],
    as_of: Optional[date] = None,
    concentration_warning_pct: float = DEFAULT_CONCENTRATION_WARNING_PCT,
    aging_over_60_warning_pct: float = DEFAULT_AGING_OVER_60_WARNING_PCT,
    dilution_warning_pct: float = DEFAULT_DILUTION_WARNING_PCT,
    collection_rate_warning_pct: float = DEFAULT_COLLECTION_RATE_WARNING_PCT,
) -> List[Dict[str, Any]]:
    """
    Covenant-style rows: METRIC / CURRENT / THRESHOLD / STATUS. Thresholds
    are configurable sample policy, not a published industry or client
    covenant — labeled as such in the UI.
    """
    concentration_rows = concentration_by_debtor(invoices, debtors, concentration_warning_pct)
    max_concentration = max((r["pct_of_open_ar"] for r in concentration_rows), default=0.0)
    max_concentration_debtor = concentration_rows[0]["debtor_name"] if concentration_rows else "n/a"

    aging = aging_distribution(invoices, as_of, aging_over_60_warning_pct)
    dilution = dilution_rate(invoices, dilution_warning_pct)
    collection = collection_rate(invoices, as_of)

    rows = [
        {
            "metric": "Open AR total",
            "current": open_ar_total(invoices),
            "threshold": "n/a (informational)",
            "status": "COMPLIANT",
        },
        {
            "metric": "Funds employed",
            "current": funds_employed(invoices),
            "threshold": "n/a (informational)",
            "status": "COMPLIANT",
        },
        {
            "metric": f"Max debtor concentration ({max_concentration_debtor})",
            "current": f"{max_concentration}%",
            "threshold": f"<= {concentration_warning_pct}%",
            "status": "WARNING" if max_concentration >= concentration_warning_pct else "COMPLIANT",
        },
        {
            "metric": "Aging over 60 days",
            "current": f"{aging['pct_over_60']}%",
            "threshold": f"<= {aging_over_60_warning_pct}%",
            "status": aging["status"],
        },
        {
            "metric": "Dilution rate",
            "current": f"{dilution}%",
            "threshold": f"<= {dilution_warning_pct}%",
            "status": "WARNING" if dilution >= dilution_warning_pct else "COMPLIANT",
        },
        {
            "metric": "Collection rate (matured invoices)",
            "current": f"{collection}%",
            "threshold": f">= {collection_rate_warning_pct}%",
            "status": "WARNING" if collection < collection_rate_warning_pct else "COMPLIANT",
        },
    ]
    return rows


def data_tape_rows(
    invoices: List[Invoice],
    debtors: Dict[str, Debtor],
    as_of: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """
    Invoice-level detail rows for LP/data-tape export: one row per invoice
    with debtor, face/advanced/paid/open amounts, aging bucket, and status.
    A plain list of dicts a caller can feed straight to csv.DictWriter.
    """
    rows = []
    for inv in invoices:
        debtor = debtors.get(inv.debtor_id)
        rows.append({
            "invoice_id": inv.invoice_id,
            "debtor_id": inv.debtor_id,
            "debtor": debtor.name if debtor else inv.debtor_id,
            "face_amount": inv.face_amount,
            "advanced_amount": inv.factored_amount,
            "paid_amount": inv.paid_amount,
            "open_amount": inv.open_amount,
            "aging_bucket": inv.aging_bucket(as_of).value,
            "status": inv.status.value,
        })
    return rows
