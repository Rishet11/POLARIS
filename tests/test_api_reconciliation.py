"""
test_api_reconciliation.py - Cash application API endpoint tests.
Tests the reconciliation POST /run endpoint, audit trail, and approval workflow.
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app
from api import state


@pytest.fixture(autouse=True)
def reset_store():
    """Autouse fixture to reset store state before each test."""
    state.store.reset()


client = TestClient(app)


def test_reconciliation_run_returns_kpis_and_payments():
    """POST /api/reconciliation/run returns KPIs and payment list."""
    response = client.post("/api/reconciliation/run")
    assert response.status_code == 200
    data = response.json()

    # Verify KPIs structure
    assert "kpis" in data
    kpis = data["kpis"]
    assert kpis["auto_applied"] == 5
    assert kpis["needs_review"] == 3
    assert kpis["exceptions"] == 2
    assert kpis["auto_match_rate"] == 50.0

    # Verify payments list
    assert "payments" in data
    assert len(data["payments"]) == 10


def test_reconciliation_run_stores_audit_trail():
    """POST /api/reconciliation/run stores audit entries."""
    response = client.post("/api/reconciliation/run")
    assert response.status_code == 200

    # Verify audit trail was populated
    assert len(state.store.audit_trail) > 0


def test_approve_review_tier_payment_creates_audit_entry():
    """POST /api/reconciliation/payments/{id}/approve on REVIEW tier creates audit entry."""
    # Run reconciliation to populate payments
    client.post("/api/reconciliation/run")

    # Find a REVIEW tier payment
    response = client.get("/api/reconciliation/payments?tier=REVIEW")
    assert response.status_code == 200
    payments = response.json()
    assert len(payments) > 0

    review_payment = payments[0]
    payment_id = review_payment["id"]

    # Approve it
    response = client.post(f"/api/reconciliation/payments/{payment_id}/approve")
    assert response.status_code == 200
    entry = response.json()
    assert entry["actor"] == "human"
    assert entry["payment_id"] == payment_id


def test_audit_trail_query_by_payment_id():
    """GET /api/reconciliation/audit-trail?q=<payment_id> filters by payment."""
    # Run reconciliation
    client.post("/api/reconciliation/run")

    # Find a REVIEW payment and approve it
    response = client.get("/api/reconciliation/payments?tier=REVIEW")
    payments = response.json()
    payment_id = payments[0]["id"]
    client.post(f"/api/reconciliation/payments/{payment_id}/approve")

    # Query audit trail for this payment
    response = client.get(f"/api/reconciliation/audit-trail?q={payment_id}")
    assert response.status_code == 200
    entries = response.json()
    assert len(entries) > 0
    assert any(e["payment_id"] == payment_id and e["actor"] == "human" for e in entries)


def test_double_approve_same_payment_returns_409():
    """POST /api/reconciliation/payments/{id}/approve twice returns 409 conflict."""
    # Run reconciliation
    client.post("/api/reconciliation/run")

    # Find a REVIEW payment
    response = client.get("/api/reconciliation/payments?tier=REVIEW")
    payments = response.json()
    payment_id = payments[0]["id"]

    # First approval succeeds
    response = client.post(f"/api/reconciliation/payments/{payment_id}/approve")
    assert response.status_code == 200

    # Second approval on same payment fails with 409
    response = client.post(f"/api/reconciliation/payments/{payment_id}/approve")
    assert response.status_code == 409


def test_reject_payment_with_reason():
    """POST /api/reconciliation/payments/{id}/reject stores reason in audit trail."""
    # Run reconciliation
    client.post("/api/reconciliation/run")

    # Find a REVIEW payment
    response = client.get("/api/reconciliation/payments?tier=REVIEW")
    payments = response.json()
    payment_id = payments[0]["id"]

    # Reject with reason
    response = client.post(
        f"/api/reconciliation/payments/{payment_id}/reject",
        json={"reason": "Debtor dispute"}
    )
    assert response.status_code == 200
    entry = response.json()
    assert entry["actor"] == "human"
    assert entry["reason"] == "Debtor dispute"
