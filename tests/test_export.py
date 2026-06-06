"""Tests for catalog glossary export (src/export_catalog_glossary.py).

Verifies the CSV export produces the correct columns, row count, and
content for downstream catalog ingestion.
"""
from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

import pytest
from rdflib import Graph, Namespace
from rdflib.namespace import RDF, SKOS

EX = Namespace("https://example.com/enterprise-ai/")

EXPECTED_COLUMNS = [
    "term_uri",
    "name",
    "definition",
    "synonyms",
    "parent_term_uri",
    "steward",
    "status",
    "last_reviewed_at",
    "review_cadence_days",
    "linked_asset_uris",
]


def _export_to_csv(graph: Graph, out_path: Path) -> list[dict]:
    """Reproduce the export logic in-process and return the rows."""
    rows = []
    for concept in graph.subjects(RDF.type, SKOS.Concept):
        status_val = graph.value(concept, EX.status)
        status = str(status_val) if status_val else ""
        if status not in {"Approved", "Deprecated"}:
            continue
        broader = graph.value(concept, SKOS.broader)
        assets = sorted(str(v) for v in graph.objects(concept, EX.implementedByAsset))
        rows.append({
            "term_uri": str(concept),
            "name": str(graph.value(concept, SKOS.prefLabel) or ""),
            "definition": str(graph.value(concept, SKOS.definition) or ""),
            "synonyms": "|".join(sorted(str(v) for v in graph.objects(concept, SKOS.altLabel))),
            "parent_term_uri": str(broader) if broader else "",
            "steward": str(graph.value(concept, EX.steward) or ""),
            "status": status,
            "last_reviewed_at": str(graph.value(concept, EX.lastReviewedAt) or ""),
            "review_cadence_days": str(graph.value(concept, EX.reviewCadenceDays) or ""),
            "linked_asset_uris": "|".join(assets),
        })
    rows.sort(key=lambda r: r["name"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=EXPECTED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return rows


# ---- column and row tests ---------------------------------------------------

class TestExportColumns:
    """The exported CSV must have the exact set of expected columns."""

    def test_csv_has_correct_columns(self, ontology_graph, tmp_path):
        out = tmp_path / "glossary.csv"
        _export_to_csv(ontology_graph, out)
        with out.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            assert list(reader.fieldnames) == EXPECTED_COLUMNS


class TestExportRowCount:
    """Only Approved or Deprecated concepts should be exported."""

    def test_exports_four_approved_concepts(self, ontology_graph, tmp_path):
        out = tmp_path / "glossary.csv"
        rows = _export_to_csv(ontology_graph, out)
        assert len(rows) == 4

    def test_rows_sorted_by_name(self, ontology_graph, tmp_path):
        out = tmp_path / "glossary.csv"
        rows = _export_to_csv(ontology_graph, out)
        names = [r["name"] for r in rows]
        assert names == sorted(names)


class TestExportContent:
    """Spot-check individual exported rows for correctness."""

    def test_customer_row_has_synonyms(self, ontology_graph, tmp_path):
        out = tmp_path / "glossary.csv"
        rows = _export_to_csv(ontology_graph, out)
        customer = next(r for r in rows if r["name"] == "Customer")
        synonyms = set(customer["synonyms"].split("|"))
        assert "Client" in synonyms
        assert "Buyer" in synonyms

    def test_active_customer_has_parent(self, ontology_graph, tmp_path):
        out = tmp_path / "glossary.csv"
        rows = _export_to_csv(ontology_graph, out)
        active = next(r for r in rows if r["name"] == "Active Customer")
        assert active["parent_term_uri"] == str(EX.CustomerTerm)

    def test_net_revenue_linked_to_asset(self, ontology_graph, tmp_path):
        out = tmp_path / "glossary.csv"
        rows = _export_to_csv(ontology_graph, out)
        revenue = next(r for r in rows if r["name"] == "Net Revenue")
        assert str(EX.RevenueMart) in revenue["linked_asset_uris"]

    def test_pii_policy_has_no_linked_asset(self, ontology_graph, tmp_path):
        out = tmp_path / "glossary.csv"
        rows = _export_to_csv(ontology_graph, out)
        pii = next(r for r in rows if r["name"] == "Customer PII Policy")
        assert pii["linked_asset_uris"] == ""

    def test_all_rows_have_status_approved(self, ontology_graph, tmp_path):
        out = tmp_path / "glossary.csv"
        rows = _export_to_csv(ontology_graph, out)
        for row in rows:
            assert row["status"] in {"Approved", "Deprecated"}


# ---- CLI integration test ---------------------------------------------------

class TestExportCLI:
    """Test export_catalog_glossary.py via subprocess."""

    def test_cli_produces_csv(self, tmp_path):
        out_file = tmp_path / "out.csv"
        result = subprocess.run(
            [sys.executable, "src/export_catalog_glossary.py", "--out", str(out_file)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert out_file.exists()
        with out_file.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 4
        assert list(reader.fieldnames) == EXPECTED_COLUMNS

    def test_cli_output_message(self, tmp_path):
        out_file = tmp_path / "out.csv"
        result = subprocess.run(
            [sys.executable, "src/export_catalog_glossary.py", "--out", str(out_file)],
            capture_output=True, text=True,
        )
        assert "Exported 4 catalog-ready glossary terms" in result.stdout
