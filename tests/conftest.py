"""Shared fixtures for the Meaning Layer starter kit test suite."""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from rdflib import Graph

# All paths are relative to the project root so tests work from a fresh clone.
ROOT = Path(__file__).resolve().parent.parent
ONTOLOGY_PATH = ROOT / "ontology" / "enterprise_ai.ttl"
SHAPES_PATH = ROOT / "ontology" / "shapes.ttl"
VALID_DATA_PATH = ROOT / "data" / "sample_data_valid.ttl"
INVALID_DATA_PATH = ROOT / "data" / "sample_data_invalid.ttl"


@pytest.fixture()
def ontology_graph() -> Graph:
    """Load the core ontology (enterprise_ai.ttl) into an rdflib Graph."""
    g = Graph()
    g.parse(ONTOLOGY_PATH, format="turtle")
    return g


@pytest.fixture()
def valid_graph() -> Graph:
    """Load the ontology plus valid sample data."""
    g = Graph()
    g.parse(ONTOLOGY_PATH, format="turtle")
    g.parse(VALID_DATA_PATH, format="turtle")
    return g


@pytest.fixture()
def invalid_graph() -> Graph:
    """Load the ontology plus both valid and invalid sample data."""
    g = Graph()
    g.parse(ONTOLOGY_PATH, format="turtle")
    g.parse(VALID_DATA_PATH, format="turtle")
    g.parse(INVALID_DATA_PATH, format="turtle")
    return g


@pytest.fixture()
def shapes_graph() -> Graph:
    """Load SHACL shapes."""
    g = Graph()
    g.parse(SHAPES_PATH, format="turtle")
    return g


@pytest.fixture(autouse=True)
def _run_from_project_root(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure every test runs with cwd set to the project root.

    This mirrors how ``make`` targets work and keeps file-path defaults
    in the source scripts functioning correctly.
    """
    monkeypatch.chdir(ROOT)
