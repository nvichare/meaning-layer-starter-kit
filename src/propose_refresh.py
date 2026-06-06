#!/usr/bin/env python3
"""Create ontology refresh proposals from stale review dates and missing catalog links."""
from __future__ import annotations
import argparse
import json
from datetime import date, timedelta
from pathlib import Path
from rdflib import Graph, Namespace
from rdflib.namespace import SKOS, RDF

EX = Namespace("https://example.com/enterprise-ai/")


def as_date(value) -> date:
    return date.fromisoformat(str(value))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of", default=date.today().isoformat())
    parser.add_argument("--ontology", default="ontology/enterprise_ai.ttl")
    parser.add_argument("--data", default="data/sample_data_valid.ttl")
    parser.add_argument("--out", default="refresh-proposals.json")
    args = parser.parse_args()
    as_of = date.fromisoformat(args.as_of)

    graph = Graph()
    graph.parse(Path(args.ontology), format="turtle")
    graph.parse(Path(args.data), format="turtle")
    proposals: list[dict] = []
    for concept in graph.subjects(RDF.type, SKOS.Concept):
        label = graph.value(concept, SKOS.prefLabel)
        reviewed = graph.value(concept, EX.lastReviewedAt)
        cadence = graph.value(concept, EX.reviewCadenceDays)
        if reviewed and cadence:
            due = as_date(reviewed) + timedelta(days=int(cadence))
            if due < as_of:
                proposals.append({
                    "type": "REVIEW_OVERDUE",
                    "concept": str(concept),
                    "label": str(label),
                    "last_reviewed": str(reviewed),
                    "review_due": due.isoformat(),
                    "recommended_action": "Assign steward review task and run lineage impact analysis before republishing.",
                })
        if (concept, EX.implementedByAsset, None) not in graph and (concept, RDF.type, EX.PolicyConcept) not in graph:
            proposals.append({
                "type": "MISSING_IMPLEMENTATION_LINK",
                "concept": str(concept),
                "label": str(label),
                "recommended_action": "Link concept to one or more catalog data assets or explicitly document why it is conceptual only.",
            })

    Path(args.out).write_text(json.dumps(proposals, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {len(proposals)} refresh proposal(s) as of {as_of}.")
    for index, proposal in enumerate(proposals, start=1):
        print(f"{index}. [{proposal['type']}] {proposal['label']}: {proposal['recommended_action']}")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
