"""Tests for SHACL validation (src/validate_graph.py).

Verifies that governed data passes validation and that deliberately
broken data triggers the expected violations.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from pyshacl import validate
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF, SKOS, SH

from tests.conftest import ONTOLOGY_PATH, SHAPES_PATH, VALID_DATA_PATH, INVALID_DATA_PATH

EX = Namespace("https://example.com/enterprise-ai/")


# ---- helpers ----------------------------------------------------------------

def _validate(data_graph: Graph, shapes_graph: Graph):
    """Run pyshacl.validate and return (conforms, results_graph, text)."""
    return validate(
        data_graph=data_graph,
        shacl_graph=shapes_graph,
        inference="rdfs",
        abort_on_first=False,
        allow_infos=True,
        allow_warnings=True,
        meta_shacl=True,
        debug=False,
    )


def _violation_messages(results_graph: Graph) -> list[str]:
    """Extract human-readable violation messages from a SHACL results graph."""
    messages = []
    for result in results_graph.subjects(RDF.type, SH.ValidationResult):
        for msg in results_graph.objects(result, SH.resultMessage):
            messages.append(str(msg))
    return sorted(messages)


def _violation_focus_nodes(results_graph: Graph) -> set[str]:
    """Extract the focus node URIs that triggered violations."""
    nodes = set()
    for result in results_graph.subjects(RDF.type, SH.ValidationResult):
        for node in results_graph.objects(result, SH.focusNode):
            nodes.add(str(node))
    return nodes


# ---- valid data tests -------------------------------------------------------

class TestValidData:
    """Valid sample data must pass all SHACL governance controls."""

    def test_valid_data_conforms(self, valid_graph, shapes_graph):
        conforms, _, _ = _validate(valid_graph, shapes_graph)
        assert conforms is True

    def test_valid_data_has_expected_triple_count(self, valid_graph):
        assert len(valid_graph) == 167

    def test_valid_data_zero_violations(self, valid_graph, shapes_graph):
        _, results_graph, _ = _validate(valid_graph, shapes_graph)
        messages = _violation_messages(results_graph)
        assert messages == []


# ---- invalid data tests -----------------------------------------------------

class TestInvalidData:
    """Invalid sample data must produce exactly 6 SHACL violations."""

    def test_invalid_data_does_not_conform(self, invalid_graph, shapes_graph):
        conforms, _, _ = _validate(invalid_graph, shapes_graph)
        assert conforms is False

    def test_invalid_data_exactly_six_violations(self, invalid_graph, shapes_graph):
        _, results_graph, _ = _validate(invalid_graph, shapes_graph)
        messages = _violation_messages(results_graph)
        assert len(messages) == 6

    def test_invalid_status_not_in_allowed_values(self, invalid_graph, shapes_graph):
        """ChurnRiskTerm has status 'Candidate' which is not Draft/Approved/Deprecated."""
        _, results_graph, _ = _validate(invalid_graph, shapes_graph)
        messages = _violation_messages(results_graph)
        assert "Lifecycle status must be Draft, Approved, or Deprecated." in messages

    def test_metric_missing_calculation_logic(self, invalid_graph, shapes_graph):
        """ChurnRiskTerm is a MetricConcept without calculationLogic."""
        _, results_graph, _ = _validate(invalid_graph, shapes_graph)
        messages = _violation_messages(results_graph)
        assert "A governed metric requires deterministic calculation logic." in messages

    def test_metric_missing_implementing_asset(self, invalid_graph, shapes_graph):
        """ChurnRiskTerm is a MetricConcept without implementedByAsset."""
        _, results_graph, _ = _validate(invalid_graph, shapes_graph)
        messages = _violation_messages(results_graph)
        assert "A governed metric must link to at least one implementing data asset." in messages

    def test_data_asset_missing_steward(self, invalid_graph, shapes_graph):
        """UnownedCustomerExport has no steward."""
        _, results_graph, _ = _validate(invalid_graph, shapes_graph)
        messages = _violation_messages(results_graph)
        assert "Each data asset requires an accountable owner or steward." in messages

    def test_data_asset_missing_asset_type(self, invalid_graph, shapes_graph):
        """UnownedCustomerExport has no assetType."""
        _, results_graph, _ = _validate(invalid_graph, shapes_graph)
        messages = _violation_messages(results_graph)
        assert "Each data asset requires an asset type." in messages

    def test_review_cadence_not_positive(self, invalid_graph, shapes_graph):
        """ChurnRiskTerm has reviewCadenceDays=0 which violates minInclusive 1."""
        _, results_graph, _ = _validate(invalid_graph, shapes_graph)
        messages = _violation_messages(results_graph)
        assert "Every governed concept requires a positive review cadence." in messages

    def test_violations_target_expected_nodes(self, invalid_graph, shapes_graph):
        """All violations should be on ChurnRiskTerm or UnownedCustomerExport."""
        _, results_graph, _ = _validate(invalid_graph, shapes_graph)
        focus_nodes = _violation_focus_nodes(results_graph)
        assert focus_nodes == {
            str(EX.ChurnRiskTerm),
            str(EX.UnownedCustomerExport),
        }


# ---- CLI integration test ---------------------------------------------------

class TestValidateCLI:
    """Test the validate_graph.py script via subprocess."""

    def test_cli_valid_returns_zero(self):
        result = subprocess.run(
            [sys.executable, "src/validate_graph.py", "--data", "data/sample_data_valid.ttl"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "SHACL conforms: True" in result.stdout

    def test_cli_invalid_returns_nonzero(self):
        result = subprocess.run(
            [sys.executable, "src/validate_graph.py",
             "--data", "data/sample_data_valid.ttl", "data/sample_data_invalid.ttl"],
            capture_output=True, text=True,
        )
        assert result.returncode == 1
        assert "SHACL conforms: False" in result.stderr or "SHACL conforms: False" in result.stdout
