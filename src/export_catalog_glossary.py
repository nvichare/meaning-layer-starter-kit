#!/usr/bin/env python3
"""Export approved SKOS concepts for catalog ingestion and steward workflows."""
from __future__ import annotations
import argparse
import csv
from pathlib import Path
from rdflib import Graph, Namespace
from rdflib.namespace import RDF, SKOS

EX = Namespace("https://example.com/enterprise-ai/")


def text(graph: Graph, subject, predicate) -> str:
    value = graph.value(subject, predicate)
    return str(value) if value is not None else ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ontology", default="ontology/enterprise_ai.ttl")
    parser.add_argument("--out", default="catalog_sync/glossary_terms.csv")
    args = parser.parse_args()
    graph = Graph().parse(Path(args.ontology), format="turtle")
    rows = []
    for concept in graph.subjects(RDF.type, SKOS.Concept):
        status = text(graph, concept, EX.status)
        if status not in {"Approved", "Deprecated"}:
            continue
        broader = graph.value(concept, SKOS.broader)
        assets = sorted(str(v) for v in graph.objects(concept, EX.implementedByAsset))
        rows.append({
            "term_uri": str(concept),
            "name": text(graph, concept, SKOS.prefLabel),
            "definition": text(graph, concept, SKOS.definition),
            "synonyms": "|".join(sorted(str(v) for v in graph.objects(concept, SKOS.altLabel))),
            "parent_term_uri": str(broader) if broader else "",
            "steward": text(graph, concept, EX.steward),
            "status": status,
            "last_reviewed_at": text(graph, concept, EX.lastReviewedAt),
            "review_cadence_days": text(graph, concept, EX.reviewCadenceDays),
            "linked_asset_uris": "|".join(assets),
        })
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda row: row["name"]))
    print(f"Exported {len(rows)} catalog-ready glossary terms to {out}")


if __name__ == "__main__":
    main()
