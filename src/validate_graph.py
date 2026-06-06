#!/usr/bin/env python3
"""Validate ontology + instance data using SHACL."""
from __future__ import annotations
import argparse
from pathlib import Path
from rdflib import Graph
from pyshacl import validate


def load_graph(paths: list[Path]) -> Graph:
    graph = Graph()
    for path in paths:
        graph.parse(path, format="turtle")
    return graph


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ontology", default="ontology/enterprise_ai.ttl")
    parser.add_argument("--shapes", default="ontology/shapes.ttl")
    parser.add_argument("--data", nargs="+", required=True)
    args = parser.parse_args()

    data_graph = load_graph([Path(args.ontology), *map(Path, args.data)])
    shapes_graph = load_graph([Path(args.shapes)])
    conforms, report_graph, report_text = validate(
        data_graph=data_graph,
        shacl_graph=shapes_graph,
        inference="rdfs",
        abort_on_first=False,
        allow_infos=True,
        allow_warnings=True,
        meta_shacl=True,
        debug=False,
    )
    print(f"SHACL conforms: {conforms}")
    print(f"Triples validated: {len(data_graph)}")
    if not conforms:
        print("\nValidation report")
        print("-----------------")
        print(report_text.strip())
        report_graph.serialize(destination="validation-report.ttl", format="turtle")
        print("\nWrote validation-report.ttl")
        return 1
    print("All ontology governance controls passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
