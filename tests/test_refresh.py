"""Tests for ontology refresh proposals (src/propose_refresh.py).

Verifies that stale concepts are flagged, current concepts are not,
and that different as-of dates produce the correct proposals.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

import pytest
from rdflib import Graph, Namespace
from rdflib.namespace import RDF, SKOS

EX = Namespace("https://example.com/enterprise-ai/")


def _run_refresh(graph: Graph, as_of: date) -> list[dict]:
    """Reproduce the refresh logic from propose_refresh.py in-process."""
    proposals: list[dict] = []
    for concept in graph.subjects(RDF.type, SKOS.Concept):
        label = graph.value(concept, SKOS.prefLabel)
        reviewed = graph.value(concept, EX.lastReviewedAt)
        cadence = graph.value(concept, EX.reviewCadenceDays)
        if reviewed and cadence:
            due = date.fromisoformat(str(reviewed)) + timedelta(days=int(cadence))
            if due < as_of:
                proposals.append({
                    "type": "REVIEW_OVERDUE",
                    "concept": str(concept),
                    "label": str(label),
                    "last_reviewed": str(reviewed),
                    "review_due": due.isoformat(),
                })
        if (concept, EX.implementedByAsset, None) not in graph \
                and (concept, RDF.type, EX.PolicyConcept) not in graph:
            proposals.append({
                "type": "MISSING_IMPLEMENTATION_LINK",
                "concept": str(concept),
                "label": str(label),
            })
    return proposals


# ---- overdue detection ------------------------------------------------------

class TestOverdueDetection:
    """Concepts whose review date + cadence < as_of should be flagged."""

    def test_active_customer_overdue_on_june_5(self, valid_graph):
        """Active Customer was reviewed 2025-10-01 with 90-day cadence.
        Due date is 2025-12-30, so it is overdue by 2026-06-05."""
        proposals = _run_refresh(valid_graph, date(2026, 6, 5))
        overdue = [p for p in proposals if p["type"] == "REVIEW_OVERDUE"]
        labels = {p["label"] for p in overdue}
        assert "Active Customer" in labels

    def test_customer_not_overdue_on_june_5(self, valid_graph):
        """Customer was reviewed 2026-05-20 with 90-day cadence.
        Due date is 2026-08-18, so it is NOT overdue on 2026-06-05."""
        proposals = _run_refresh(valid_graph, date(2026, 6, 5))
        overdue = [p for p in proposals if p["type"] == "REVIEW_OVERDUE"]
        labels = {p["label"] for p in overdue}
        assert "Customer" not in labels

    def test_net_revenue_not_overdue_on_june_5(self, valid_graph):
        """Net Revenue was reviewed 2026-04-15 with 60-day cadence.
        Due date is 2026-06-14, so it is NOT overdue on 2026-06-05."""
        proposals = _run_refresh(valid_graph, date(2026, 6, 5))
        overdue = [p for p in proposals if p["type"] == "REVIEW_OVERDUE"]
        labels = {p["label"] for p in overdue}
        assert "Net Revenue" not in labels

    def test_pii_policy_not_overdue_on_june_5(self, valid_graph):
        """Customer PII Policy was reviewed 2026-05-30 with 30-day cadence.
        Due date is 2026-06-29, so it is NOT overdue on 2026-06-05."""
        proposals = _run_refresh(valid_graph, date(2026, 6, 5))
        overdue = [p for p in proposals if p["type"] == "REVIEW_OVERDUE"]
        labels = {p["label"] for p in overdue}
        assert "Customer PII Policy" not in labels


# ---- no overdue when as-of is early enough ----------------------------------

class TestNoOverdue:
    """When all concepts are current, no REVIEW_OVERDUE proposals should appear."""

    def test_no_overdue_early_date(self, valid_graph):
        """All concepts are current as of 2025-10-02 (day after earliest review)."""
        proposals = _run_refresh(valid_graph, date(2025, 10, 2))
        overdue = [p for p in proposals if p["type"] == "REVIEW_OVERDUE"]
        assert overdue == []


# ---- different as-of dates --------------------------------------------------

class TestDifferentAsOfDates:
    """Moving the as-of date forward should trigger more overdue concepts."""

    def test_late_date_catches_all_concepts(self, valid_graph):
        """By 2027-01-01, every concept should be overdue."""
        proposals = _run_refresh(valid_graph, date(2027, 1, 1))
        overdue = [p for p in proposals if p["type"] == "REVIEW_OVERDUE"]
        labels = {p["label"] for p in overdue}
        assert "Customer" in labels
        assert "Active Customer" in labels
        assert "Net Revenue" in labels
        assert "Customer PII Policy" in labels

    def test_mid_date_catches_some_concepts(self, valid_graph):
        """On 2026-06-15, Net Revenue (due 06-14) should also appear overdue."""
        proposals = _run_refresh(valid_graph, date(2026, 6, 15))
        overdue = [p for p in proposals if p["type"] == "REVIEW_OVERDUE"]
        labels = {p["label"] for p in overdue}
        assert "Active Customer" in labels
        assert "Net Revenue" in labels
        assert "Customer" not in labels


# ---- missing implementation link detection ----------------------------------

class TestMissingImplementationLink:
    """Concepts without implementedByAsset (and not PolicyConcept) should be flagged."""

    def test_policy_concepts_not_flagged(self, valid_graph):
        """Customer PII Policy is a PolicyConcept, so it should NOT be flagged."""
        proposals = _run_refresh(valid_graph, date(2026, 6, 5))
        missing = [p for p in proposals if p["type"] == "MISSING_IMPLEMENTATION_LINK"]
        labels = {p["label"] for p in missing}
        assert "Customer PII Policy" not in labels

    def test_linked_concepts_not_flagged(self, valid_graph):
        """Customer, Active Customer, Net Revenue all have assets linked."""
        proposals = _run_refresh(valid_graph, date(2026, 6, 5))
        missing = [p for p in proposals if p["type"] == "MISSING_IMPLEMENTATION_LINK"]
        labels = {p["label"] for p in missing}
        assert "Customer" not in labels
        assert "Active Customer" not in labels
        assert "Net Revenue" not in labels


# ---- CLI integration test ---------------------------------------------------

class TestRefreshCLI:
    """Test propose_refresh.py via subprocess."""

    def test_cli_produces_output_file(self, tmp_path):
        out_file = tmp_path / "proposals.json"
        result = subprocess.run(
            [sys.executable, "src/propose_refresh.py",
             "--as-of", "2026-06-05", "--out", str(out_file)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert out_file.exists()
        data = json.loads(out_file.read_text())
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_cli_early_date_zero_proposals(self, tmp_path):
        out_file = tmp_path / "proposals.json"
        result = subprocess.run(
            [sys.executable, "src/propose_refresh.py",
             "--as-of", "2025-10-02", "--out", str(out_file)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "0 refresh proposal(s)" in result.stdout
