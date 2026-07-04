"""
test_api_portfolio.py - Portfolio monitor API endpoint tests.
Tests covenants, aging, data-tape CSV export, and parity with direct imports.
"""

import csv
import io
import pytest
from fastapi.testclient import TestClient
from api.main import app
from api import state
from factoring.portfolio import covenant_table


@pytest.fixture(autouse=True)
def reset_store():
    """Autouse fixture to reset store state before each test."""
    state.store.reset()


client = TestClient(app)


def test_covenants_returns_six_rows():
    """GET /api/portfolio/covenants returns 6 covenant rows."""
    response = client.get("/api/portfolio/covenants")
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 6
    # Verify structure of first row
    assert "metric" in rows[0]
    assert "current" in rows[0]
    assert "threshold" in rows[0]
    assert "status" in rows[0]


def test_aging_has_required_keys():
    """GET /api/portfolio/aging returns aging distribution with required keys."""
    response = client.get("/api/portfolio/aging")
    assert response.status_code == 200
    data = response.json()
    required_keys = ["CURRENT", "1-30", "31-60", "61-90", "90+"]
    for key in required_keys:
        assert key in data
        assert "count" in data[key]
        assert "amount" in data[key]
        assert "pct_of_open_ar" in data[key]


def test_data_tape_csv_export():
    """GET /api/portfolio/data-tape.csv returns CSV with 14 invoices + header."""
    response = client.get("/api/portfolio/data-tape.csv")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"

    # Parse CSV
    csv_string = response.text
    reader = csv.DictReader(io.StringIO(csv_string))
    rows = list(reader)

    # Verify row count
    assert len(rows) == 14

    # Verify header starts with invoice_id
    fieldnames = reader.fieldnames
    assert fieldnames[0] == "invoice_id"


def test_data_tape_csv_has_required_columns():
    """CSV export includes all required columns."""
    response = client.get("/api/portfolio/data-tape.csv")
    csv_string = response.text
    reader = csv.DictReader(io.StringIO(csv_string))
    fieldnames = reader.fieldnames

    required_fields = ["invoice_id", "debtor_id", "debtor", "face_amount",
                       "advanced_amount", "paid_amount", "open_amount",
                       "aging_bucket", "status"]
    for field in required_fields:
        assert field in fieldnames


def test_covenant_parity_with_direct_import():
    """Covenant API response matches direct portfolio.covenant_table call."""
    # API response
    response = client.get("/api/portfolio/covenants")
    api_rows = response.json()

    # Direct import
    direct_rows = covenant_table(state.store.invoices, state.store.debtors)

    # Verify same count
    assert len(api_rows) == len(direct_rows) == 6

    # Verify same metrics in same order
    for api_row, direct_row in zip(api_rows, direct_rows):
        assert api_row["metric"] == direct_row["metric"]
        assert api_row["status"] == direct_row["status"]


def test_summary_returns_open_ar_and_funds_employed():
    """GET /api/portfolio/summary returns open_ar_total and funds_employed."""
    response = client.get("/api/portfolio/summary")
    assert response.status_code == 200
    data = response.json()
    assert "open_ar_total" in data
    assert "funds_employed" in data
    assert isinstance(data["open_ar_total"], (int, float))
    assert isinstance(data["funds_employed"], (int, float))


def test_concentration_returns_debtor_rows():
    """GET /api/portfolio/concentration returns per-debtor concentration."""
    response = client.get("/api/portfolio/concentration")
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) > 0
    # Verify structure
    for row in rows:
        assert "debtor_id" in row
        assert "debtor_name" in row
        assert "open_amount" in row
        assert "pct_of_open_ar" in row
        assert "status" in row
