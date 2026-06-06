"""Tests for concept querying (src/query_context.py).

Verifies SPARQL-based lookups against the governed ontology return the
correct concept metadata for agents and humans alike.
"""
from __future__ import annotations

import json
import subprocess
import sys

import pytest
from rdflib import Graph, Literal, Namespace
from rdflib.namespace import SKOS

EX = Namespace("https://example.com/enterprise-ai/")

QUERY = """
PREFIX ex: <https://example.com/enterprise-ai/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT ?term ?label ?definition ?steward ?status ?logic ?asset ?catalogId
WHERE {
  ?term a skos:Concept ;
        skos:prefLabel ?label ;
        skos:definition ?definition ;
        ex:steward ?steward ;
        ex:status ?status .
  FILTER(CONTAINS(LCASE(STR(?label)), LCASE(?needle)))
  OPTIONAL { ?term ex:calculationLogic ?logic . }
  OPTIONAL { ?term ex:implementedByAsset ?asset .
             OPTIONAL { ?asset ex:catalogId ?catalogId . } }
}
ORDER BY ?label
"""


def _query(graph: Graph, needle: str) -> list[dict]:
    """Run the governed concept query and return structured results."""
    rows = graph.query(QUERY, initBindings={"needle": Literal(needle)})
    return [
        {
            "concept_uri": str(r.term),
            "label": str(r.label),
            "definition": str(r.definition),
            "steward": str(r.steward),
            "status": str(r.status),
            "calculation_logic": str(r.logic) if r.logic else None,
            "asset_uri": str(r.asset) if r.asset else None,
            "catalog_id": str(r.catalogId) if r.catalogId else None,
        }
        for r in rows
    ]


# ---- individual concept tests -----------------------------------------------

class TestQueryCustomer:
    """Querying 'customer' should return Customer, Active Customer, and Customer PII Policy."""

    def test_customer_returns_three_results(self, valid_graph):
        results = _query(valid_graph, "customer")
        assert len(results) == 3

    def test_customer_labels(self, valid_graph):
        results = _query(valid_graph, "customer")
        labels = {r["label"] for r in results}
        assert labels == {"Customer", "Active Customer", "Customer PII Policy"}

    def test_customer_term_has_correct_steward(self, valid_graph):
        results = _query(valid_graph, "customer")
        customer = next(r for r in results if r["label"] == "Customer")
        assert customer["steward"] == "Customer Data Council"

    def test_customer_term_links_to_master_table(self, valid_graph):
        results = _query(valid_graph, "customer")
        customer = next(r for r in results if r["label"] == "Customer")
        assert customer["asset_uri"] == str(EX.CustomerMasterTable)
        assert customer["catalog_id"] == "snowflake.prod_crm.customer_master"


class TestQueryActiveCustomer:
    """Querying 'active customer' should return the Active Customer concept."""

    def test_active_customer_returns_one_result(self, valid_graph):
        results = _query(valid_graph, "active customer")
        assert len(results) == 1

    def test_active_customer_definition(self, valid_graph):
        results = _query(valid_graph, "active customer")
        assert "trailing 12 months" in results[0]["definition"]

    def test_active_customer_steward(self, valid_graph):
        results = _query(valid_graph, "active customer")
        assert results[0]["steward"] == "Growth Analytics"


class TestQueryNetRevenue:
    """Querying 'net revenue' should return the metric with calculation logic."""

    def test_net_revenue_returns_one_result(self, valid_graph):
        results = _query(valid_graph, "net revenue")
        assert len(results) == 1

    def test_net_revenue_has_calculation_logic(self, valid_graph):
        results = _query(valid_graph, "net revenue")
        assert results[0]["calculation_logic"] is not None
        assert "SUM" in results[0]["calculation_logic"]

    def test_net_revenue_links_to_revenue_mart(self, valid_graph):
        results = _query(valid_graph, "net revenue")
        assert results[0]["asset_uri"] == str(EX.RevenueMart)
        assert results[0]["catalog_id"] == "snowflake.finance.revenue_mart"

    def test_net_revenue_steward_is_finance(self, valid_graph):
        results = _query(valid_graph, "net revenue")
        assert results[0]["steward"] == "Finance Analytics"


class TestQueryPIIPolicy:
    """Querying 'pii' should return the Customer PII Policy concept."""

    def test_pii_returns_one_result(self, valid_graph):
        results = _query(valid_graph, "pii")
        assert len(results) == 1

    def test_pii_policy_has_no_asset(self, valid_graph):
        results = _query(valid_graph, "pii")
        assert results[0]["asset_uri"] is None
        assert results[0]["catalog_id"] is None

    def test_pii_policy_steward_is_privacy_office(self, valid_graph):
        results = _query(valid_graph, "pii")
        assert results[0]["steward"] == "Privacy Office"


class TestQueryNotFound:
    """Querying a term that does not exist should return an empty list."""

    def test_nonexistent_returns_empty(self, valid_graph):
        results = _query(valid_graph, "nonexistent")
        assert results == []

    def test_gibberish_returns_empty(self, valid_graph):
        results = _query(valid_graph, "xyzzy12345")
        assert results == []


# ---- CLI integration test ---------------------------------------------------

class TestQueryCLI:
    """Test query_context.py via subprocess."""

    def test_cli_revenue_returns_json(self):
        result = subprocess.run(
            [sys.executable, "src/query_context.py", "revenue"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert len(data) == 1
        assert data[0]["label"] == "Net Revenue"

    def test_cli_nonexistent_returns_empty_list(self):
        result = subprocess.run(
            [sys.executable, "src/query_context.py", "nonexistent"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data == []
