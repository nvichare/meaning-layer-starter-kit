#!/usr/bin/env python3
"""Preview Atlan Business Graph CSV rows from approved ontology concepts.

For production, load this CSV with Atlan Asset Import for glossaries or translate the
same rows into pyatlan AtlasGlossaryTerm creator/update calls for your tenant.
"""
from __future__ import annotations
import argparse
import csv
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="catalog_sync/glossary_terms.csv")
    parser.add_argument("--out", default="catalog_sync/atlan_business_graph_import.csv")
    parser.add_argument("--glossary", default="Enterprise Business Vocabulary")
    args = parser.parse_args()
    rows = list(csv.DictReader(Path(args.csv).open(encoding="utf-8")))
    output = []
    for row in rows:
        output.append({
            "Glossary": args.glossary,
            "Term": row["name"],
            "Definition": row["definition"],
            "Synonyms": row["synonyms"],
            "Status": row["status"],
            "Steward": row["steward"],
            "Ontology URI": row["term_uri"],
            "Linked Assets": row["linked_asset_uris"],
        })
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output[0].keys()))
        writer.writeheader()
        writer.writerows(output)
    print(f"Prepared {len(output)} Atlan Business Graph import row(s) at {out}")


if __name__ == "__main__":
    main()
