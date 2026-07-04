import csv
import io
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from api.state import store
from factoring.portfolio import (
    open_ar_total,
    funds_employed,
    covenant_table,
    concentration_by_debtor,
    aging_distribution,
    data_tape_rows,
)

router = APIRouter(prefix="/api/portfolio")


@router.get("/summary")
def summary():
    """Return open_ar_total and funds_employed."""
    return {
        "open_ar_total": open_ar_total(store.invoices),
        "funds_employed": funds_employed(store.invoices),
    }


@router.get("/covenants")
def covenants():
    """Return covenant_table (metrics with thresholds and status)."""
    return covenant_table(store.invoices, store.debtors)


@router.get("/concentration")
def concentration():
    """Return concentration_by_debtor (open AR concentration per account)."""
    return concentration_by_debtor(store.invoices, store.debtors)


@router.get("/aging")
def aging():
    """Return aging_distribution (aging bucket distribution)."""
    return aging_distribution(store.invoices)


@router.get("/data-tape.csv")
def data_tape_csv():
    """Return data-tape export as CSV (streaming response)."""
    rows = data_tape_rows(store.invoices, store.debtors)

    # Build CSV in memory
    output = io.StringIO()
    if rows:
        fieldnames = list(rows[0].keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    csv_string = output.getvalue()

    return StreamingResponse(
        iter([csv_string]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=polaris_data_tape.csv"},
    )
