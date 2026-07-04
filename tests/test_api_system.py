"""
test_api_system.py - System health and configuration endpoint tests.
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


def test_health_returns_ok_status():
    """GET /api/health returns {"status":"ok"}."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_config_returns_demo_mode():
    """GET /api/config reflects the actual config.DEMO_MODE flag."""
    import config

    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert "demo_mode" in data
    assert data["demo_mode"] == config.DEMO_MODE


def test_reset_returns_payment_and_invoice_counts():
    """POST /api/reset returns payments and invoices_open counts."""
    response = client.post("/api/reset")
    assert response.status_code == 200
    data = response.json()
    assert "payments" in data
    assert "invoices_open" in data
    assert data["payments"] == 10
    assert data["invoices_open"] == 14
