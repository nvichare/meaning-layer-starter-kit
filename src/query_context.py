#!/usr/bin/env python3
"""Return governed context that an AI agent can use at runtime."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from rdflib import Graph, Namespace, Literal
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("needle", help="Concept label fragment, for example revenue")
    parser.add_argument("--ontology", default="ontology/enterprise_ai.ttl")
    parser.add_argument("--data", default="data/sample_data_valid.ttl")
    args = parser.parse_args()

    graph = Graph()
    graph.parse(Path(args.ontology), format="turtle")
    graph.parse(Path(args.data), format="turtle")
    rows = graph.query(QUERY, initBindings={"needle": Literal(args.needle)})
    result = []
    for row in rows:
        result.append({
            "concept_uri": str(row.term),
            "label": str(row.label),
            "definition": str(row.definition),
            "steward": str(row.steward),
            "status": str(row.status),
            "calculation_logic": str(row.logic) if row.logic else None,
            "asset_uri": str(row.asset) if row.asset else None,
            "catalog_id": str(row.catalogId) if row.catalogId else None,
        })
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
