"""
test_api_collections.py - Collections workflow API endpoint tests.
Tests build-queue, send-reminder, duplicate-send blocking, and escalation guards.
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


def test_build_queue_returns_cases():
    """POST /api/collections/build-queue returns prioritized cases."""
    response = client.post("/api/collections/build-queue")
    assert response.status_code == 200
    cases = response.json()
    assert len(cases) == 10


def test_send_reminder_on_case():
    """POST /api/collections/cases/{id}/send-reminder returns 200 and updates log."""
    # Build queue
    response = client.post("/api/collections/build-queue")
    cases = response.json()
    case_id = cases[0]["case_id"]

    # Send reminder
    response = client.post(
        f"/api/collections/cases/{case_id}/send-reminder",
        json={"language": "en"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["outcome"] == "OK"
    assert "message" in data


def test_retry_duplicate_send_blocks_identical_message():
    """POST /api/collections/cases/{id}/retry-duplicate-send blocks duplicate."""
    # Build queue
    response = client.post("/api/collections/build-queue")
    cases = response.json()
    case_id = cases[0]["case_id"]

    # Send a reminder
    response = client.post(
        f"/api/collections/cases/{case_id}/send-reminder",
        json={"language": "en"}
    )
    assert response.status_code == 200

    # Retry the same message
    response = client.post(
        f"/api/collections/cases/{case_id}/retry-duplicate-send"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["outcome"] == "BLOCKED_DUPLICATE_MESSAGE"


def test_escalate_before_required_attempts_blocks():
    """POST /api/collections/cases/{id}/escalate after 1 attempt returns BLOCKED."""
    # Build a fresh queue
    response = client.post("/api/collections/build-queue")
    cases = response.json()
    case_id = cases[0]["case_id"]

    # Send one reminder to enter AWAIT_RESPONSE state
    client.post(
        f"/api/collections/cases/{case_id}/send-reminder",
        json={"language": "en"}
    )

    # Attempt escalation after only 1 outreach (gate requires 2+)
    response = client.post(f"/api/collections/cases/{case_id}/escalate")
    assert response.status_code == 200
    data = response.json()
    assert data["outcome"] == "BLOCKED_ESCALATION_GATE"


def test_list_cases_returns_all():
    """GET /api/collections/cases lists all cases after build-queue."""
    client.post("/api/collections/build-queue")
    response = client.get("/api/collections/cases")
    assert response.status_code == 200
    cases = response.json()
    assert len(cases) > 0


def test_case_detail_includes_history_and_log():
    """GET /api/collections/cases/{id} includes history and log."""
    response = client.post("/api/collections/build-queue")
    cases = response.json()
    case_id = cases[0]["case_id"]

    # Send reminder to create log entry
    client.post(
        f"/api/collections/cases/{case_id}/send-reminder",
        json={"language": "en"}
    )

    # Get case detail
    response = client.get(f"/api/collections/cases/{case_id}")
    assert response.status_code == 200
    data = response.json()
    assert "case_id" in data
    assert "history" in data
    assert "log" in data
    assert len(data["log"]) > 0
