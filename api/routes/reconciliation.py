"""
Reconciliation (cash application) routes over the existing rule-based
ReconciliationAgent. No matching logic lives here: this module only
runs the engine, serializes its output, and mutates store state through
apply_match / reject_match exactly as app.py does.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from factoring.models import MatchTier
from factoring.reconciliation_agent import ReconciliationAgent, apply_match, reject_match

from api.serializers import audit_entry_to_dict, payment_to_dict
from api.state import store

router = APIRouter(prefix="/api/reconciliation", tags=["reconciliation"])


class RejectBody(BaseModel):
    reason: str


def _invoices_by_id():
    return {i.invoice_id: i for i in store.invoices}


def _find_payment(payment_id: str):
    for p in store.payments:
        if p.payment_id == payment_id:
            return p
    raise HTTPException(status_code=404, detail=f"payment {payment_id} not found")


@router.post("/run")
def run_reconciliation():
    # Matching always runs against the pristine bank feed, so every run yields
    # the same deterministic result regardless of prior approve/reject actions
    # or a previous run in the same session. reset() rebuilds the dataset from
    # get_back_office_dataset() and clears the audit trail.
    store.reset()
    agent = ReconciliationAgent()
    result = agent.process(store.payments, store.invoices, store.debtors)
    store.recon_result = result
    store.audit_trail.extend(result["audit_trail"])

    kpis = result["kpis"]
    invoices_by_id = _invoices_by_id()
    return {
        "kpis": {
            "auto_match_rate": kpis["auto_match_rate"],
            "auto_applied": kpis["auto_applied"],
            "needs_review": kpis["review"],
            "exceptions": kpis["exceptions"],
        },
        "payments": [payment_to_dict(p, invoices_by_id) for p in result["results"]],
    }


@router.get("/payments")
def list_payments(tier: Optional[str] = "ALL"):
    invoices_by_id = _invoices_by_id()
    payments = store.payments

    if tier and tier != "ALL":
        try:
            tier_enum = MatchTier[tier]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"invalid tier {tier}")
        payments = [p for p in payments if p.match_tier == tier_enum]

    return [payment_to_dict(p, invoices_by_id) for p in payments]


@router.post("/payments/{payment_id}/approve")
def approve_payment(payment_id: str):
    payment = _find_payment(payment_id)
    try:
        entry = apply_match(payment, store.invoices, actor="human")
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    store.audit_trail.append(entry)
    return audit_entry_to_dict(entry)


@router.post("/payments/{payment_id}/reject")
def reject_payment(payment_id: str, body: RejectBody):
    payment = _find_payment(payment_id)
    try:
        entry = reject_match(payment, body.reason, actor="human")
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    store.audit_trail.append(entry)
    return audit_entry_to_dict(entry)


@router.post("/payments/{payment_id}/approve-first-candidate")
def approve_first_candidate(payment_id: str):
    payment = _find_payment(payment_id)
    invoices_by_id = _invoices_by_id()
    candidates = [invoices_by_id[iid] for iid in payment.matched_invoice_ids if iid in invoices_by_id]

    if not candidates:
        raise HTTPException(status_code=400, detail=f"{payment_id} has no candidate invoices")

    payment.matched_invoice_ids = [candidates[0].invoice_id]
    try:
        entry = apply_match(payment, store.invoices, actor="human")
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    store.audit_trail.append(entry)
    return audit_entry_to_dict(entry)


@router.get("/audit-trail")
def get_audit_trail(q: Optional[str] = None):
    trail = store.audit_trail
    if q:
        query = q.lower()
        trail = [
            e for e in trail
            if query in str(e.get("payment_id", "")).lower()
            or query in " ".join(e.get("invoice_ids", [])).lower()
            or query in str(e.get("actor", "")).lower()
            or query in str(e.get("reason", "")).lower()
            or query in str(e.get("tier", "")).lower()
        ]

    ordered = sorted(trail, key=lambda e: e["timestamp"], reverse=True)
    return [audit_entry_to_dict(e) for e in ordered]
