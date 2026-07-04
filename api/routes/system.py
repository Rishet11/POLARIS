"""
System configuration and state management routes.
"""

from fastapi import APIRouter
from api.state import store
from config import DEMO_MODE
from factoring.models import InvoiceStatus


router = APIRouter(prefix="/api")


@router.get("/config")
def get_config():
    """Return system configuration including demo mode status."""
    return {"demo_mode": DEMO_MODE}


@router.post("/reset")
def reset_system():
    """Reset system state to initial dataset and return counts."""
    store.reset()

    # Count invoices with open/unpaid status
    invoices_open = sum(
        1 for inv in store.invoices
        if inv.status in (InvoiceStatus.OUTSTANDING, InvoiceStatus.PARTIAL, InvoiceStatus.SHORT_PAY)
    )

    return {
        "payments": len(store.payments),
        "invoices_open": invoices_open,
    }
