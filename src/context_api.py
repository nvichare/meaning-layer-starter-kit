#!/usr/bin/env python3
"""Minimal agent-facing context API backed by governed RDF."""
from __future__ import annotations
from pathlib import Path
from fastapi import FastAPI, HTTPException
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import SKOS

EX = Namespace("https://example.com/enterprise-ai/")
app = FastAPI(title="Enterprise Meaning Layer API", version="0.1.0")
graph = Graph()
graph.parse(Path("ontology/enterprise_ai.ttl"), format="turtle")
graph.parse(Path("data/sample_data_valid.ttl"), format="turtle")


def literal(subject, predicate):
    value = graph.value(subject, predicate)
    return str(value) if value is not None else None


@app.get("/concepts/{concept_name}")
def get_concept(concept_name: str):
    candidates = [s for s, _, label in graph.triples((None, SKOS.prefLabel, None)) if str(label).lower() == concept_name.lower()]
    if not candidates:
        raise HTTPException(status_code=404, detail="Concept not found")
    concept = candidates[0]
    assets = []
    for asset in graph.objects(concept, EX.implementedByAsset):
        assets.append({
            "uri": str(asset),
            "catalog_id": literal(asset, EX.catalogId),
            "source_system": literal(asset, EX.sourceSystem),
            "asset_type": literal(asset, EX.assetType),
        })
    return {
        "uri": str(concept),
        "label": literal(concept, SKOS.prefLabel),
        "definition": literal(concept, SKOS.definition),
        "status": literal(concept, EX.status),
        "steward": literal(concept, EX.steward),
        "calculation_logic": literal(concept, EX.calculationLogic),
        "last_reviewed_at": literal(concept, EX.lastReviewedAt),
        "review_cadence_days": literal(concept, EX.reviewCadenceDays),
        "implemented_by_assets": assets,
    }
