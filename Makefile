.PHONY: validate validate-invalid query refresh export sync-openmetadata sync-atlan api test all

validate:
	python src/validate_graph.py --data data/sample_data_valid.ttl

validate-invalid:
	python src/validate_graph.py --data data/sample_data_valid.ttl data/sample_data_invalid.ttl

query:
	python src/query_context.py revenue

refresh:
	python src/propose_refresh.py --as-of 2026-06-05

export:
	python src/export_catalog_glossary.py

sync-openmetadata: export
	python src/sync_openmetadata.py

sync-atlan: export
	python src/sync_atlan.py

api:
	uvicorn src.context_api:app --reload

test:
	python -m pytest tests/ -v

all: validate query refresh export test
