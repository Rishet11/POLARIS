"""
Plain serializer functions: dataclass/enum objects -> JSON-safe dicts.
No business logic here, just field extraction matching the real
dataclasses in factoring/models.py and the audit entries produced by
factoring/reconciliation_agent.py.
"""

from typing import Any, Dict, List

from factoring.models import BankPayment, Invoice


def invoice_to_dict(inv: Invoice) -> Dict[str, Any]:
    return {
        "invoice_id": inv.invoice_id,
        "debtor_id": inv.debtor_id,
        "face_amount": inv.face_amount,
        "invoice_date": inv.invoice_date.isoformat(),
        "due_date": inv.due_date.isoformat(),
        "reference_no": inv.reference_no,
        "advance_rate": inv.advance_rate,
        "status": inv.status.value,
        "paid_amount": inv.paid_amount,
        "factored_amount": inv.factored_amount,
        "open_amount": inv.open_amount,
        "is_open": inv.is_open,
    }


def payment_to_dict(p: BankPayment, invoices_by_id: Dict[str, Invoice]) -> Dict[str, Any]:
    candidates = []
    for iid in p.matched_invoice_ids:
        inv = invoices_by_id.get(iid)
        if inv is not None:
            candidates.append({"invoice_id": inv.invoice_id, "open_amount": inv.open_amount})

    return {
        "id": p.payment_id,
        "payer": p.payer_name,
        "amount": p.amount,
        "value_date": p.value_date.isoformat(),
        "memo": p.reference_text,
        "reference": p.reference_text,
        "match_tier": p.match_tier.value if p.match_tier else None,
        "confidence": p.match_confidence,
        "matched_invoice_ids": list(p.matched_invoice_ids),
        "match_reason": p.match_reason,
        "applied": p.applied,
        "matched_invoice_candidates": candidates,
    }


def audit_entry_to_dict(e: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "timestamp": e.get("timestamp"),
        "actor": e.get("actor"),
        "payment_id": e.get("payment_id"),
        "invoice_ids": list(e.get("invoice_ids", [])),
        "tier": e.get("tier"),
        "confidence": e.get("confidence"),
        "reason": e.get("reason"),
    }
