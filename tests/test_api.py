"""Tests for the FastAPI context API (src/context_api.py).

Uses Starlette's TestClient to exercise the /concepts/{name} endpoint
without starting a real server.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.context_api import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Create a test client for the context API."""
    return TestClient(app)


# ---- successful lookups -----------------------------------------------------

class TestGetNetRevenue:
    """GET /concepts/net revenue should return the Net Revenue concept."""

    def test_status_code_200(self, client):
        response = client.get("/concepts/net revenue")
        assert response.status_code == 200

    def test_label(self, client):
        data = client.get("/concepts/net revenue").json()
        assert data["label"] == "Net Revenue"

    def test_definition_present(self, client):
        data = client.get("/concepts/net revenue").json()
        assert "gross revenue" in data["definition"].lower()

    def test_calculation_logic_present(self, client):
        data = client.get("/concepts/net revenue").json()
        assert data["calculation_logic"] is not None
        assert "SUM" in data["calculation_logic"]

    def test_steward(self, client):
        data = client.get("/concepts/net revenue").json()
        assert data["steward"] == "Finance Analytics"

    def test_status_approved(self, client):
        data = client.get("/concepts/net revenue").json()
        assert data["status"] == "Approved"

    def test_has_implementing_asset(self, client):
        data = client.get("/concepts/net revenue").json()
        assert len(data["implemented_by_assets"]) >= 1
        asset = data["implemented_by_assets"][0]
        assert "RevenueMart" in asset["uri"]
        assert asset["catalog_id"] == "snowflake.finance.revenue_mart"


class TestGetCustomer:
    """GET /concepts/customer should return the Customer concept."""

    def test_status_code_200(self, client):
        response = client.get("/concepts/customer")
        assert response.status_code == 200

    def test_label(self, client):
        data = client.get("/concepts/customer").json()
        assert data["label"] == "Customer"

    def test_steward(self, client):
        data = client.get("/concepts/customer").json()
        assert data["steward"] == "Customer Data Council"

    def test_has_implementing_asset(self, client):
        data = client.get("/concepts/customer").json()
        assert len(data["implemented_by_assets"]) >= 1

    def test_review_cadence(self, client):
        data = client.get("/concepts/customer").json()
        assert data["review_cadence_days"] == "90"


class TestGetActiveCustomer:
    """GET /concepts/active customer should return the Active Customer concept."""

    def test_status_code_200(self, client):
        response = client.get("/concepts/active customer")
        assert response.status_code == 200

    def test_label(self, client):
        data = client.get("/concepts/active customer").json()
        assert data["label"] == "Active Customer"


class TestGetPIIPolicy:
    """GET /concepts/customer pii policy should return the policy concept."""

    def test_status_code_200(self, client):
        response = client.get("/concepts/customer pii policy")
        assert response.status_code == 200

    def test_no_implementing_assets(self, client):
        data = client.get("/concepts/customer pii policy").json()
        assert data["implemented_by_assets"] == []


# ---- case insensitivity -----------------------------------------------------

class TestCaseInsensitive:
    """The API should match concept names regardless of case."""

    def test_uppercase(self, client):
        response = client.get("/concepts/NET REVENUE")
        assert response.status_code == 200

    def test_mixed_case(self, client):
        response = client.get("/concepts/Net Revenue")
        assert response.status_code == 200

    def test_lowercase(self, client):
        response = client.get("/concepts/net revenue")
        assert response.status_code == 200


# ---- not found --------------------------------------------------------------

class TestNotFound:
    """GET /concepts/nonexistent should return 404."""

    def test_nonexistent_returns_404(self, client):
        response = client.get("/concepts/nonexistent")
        assert response.status_code == 404

    def test_404_has_detail_message(self, client):
        data = client.get("/concepts/nonexistent").json()
        assert "not found" in data["detail"].lower()

    def test_empty_name_returns_404(self, client):
        response = client.get("/concepts/xyzzy12345")
        assert response.status_code == 404
