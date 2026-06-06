#!/usr/bin/env python3
"""Create or preview OpenMetadata glossary term payloads from approved ontology concepts.

Default behavior is dry-run. Use --apply only after setting OPENMETADATA_BASE_URL and
OPENMETADATA_TOKEN and reviewing the payload against your tenant's API version.
"""
from __future__ import annotations
import argparse
import csv
import json
import os
from pathlib import Path
import requests


def payload(row: dict[str, str], glossary_name: str) -> dict:
    return {
        "name": row["name"].replace(" ", ""),
        "displayName": row["name"],
        "description": row["definition"],
        "glossary": glossary_name,
        "synonyms": [v for v in row["synonyms"].split("|") if v],
        "references": [{"name": "Ontology URI", "endpoint": row["term_uri"]}],
        "extension": {
            "ontologyUri": row["term_uri"],
            "steward": row["steward"],
            "lastReviewedAt": row["last_reviewed_at"],
            "reviewCadenceDays": row["review_cadence_days"],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="catalog_sync/glossary_terms.csv")
    parser.add_argument("--glossary", default="EnterpriseBusinessVocabulary")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    base_url = os.getenv("OPENMETADATA_BASE_URL", "https://openmetadata.example/api")
    token = os.getenv("OPENMETADATA_TOKEN")
    rows = list(csv.DictReader(Path(args.csv).open(encoding="utf-8")))
    for row in rows:
        body = payload(row, args.glossary)
        if not args.apply:
            print(json.dumps(body, indent=2))
            continue
        if not token:
            raise SystemExit("OPENMETADATA_TOKEN is required with --apply")
        response = requests.post(
            f"{base_url.rstrip('/')}/v1/glossaryTerms",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=body,
            timeout=30,
        )
        response.raise_for_status()
        print(f"Upserted {row['name']}: HTTP {response.status_code}")


if __name__ == "__main__":
    main()
