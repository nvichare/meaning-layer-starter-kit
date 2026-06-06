# Testing Guide -- The Meaning Layer Starter Kit

This document covers how to run the test suite, what to expect, and how to
extend it as your ontology grows.

## Prerequisites

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The `requirements.txt` includes `pytest` and `httpx` (needed by FastAPI's
TestClient).

## Running the full test suite

```bash
# Verbose output showing every test name
python -m pytest tests/ -v

# Or via Make
make test
```

Expected result: **75 passed** in approximately 4 seconds.

## Running individual test files

```bash
python -m pytest tests/test_validate.py -v   # 13 SHACL validation tests
python -m pytest tests/test_query.py -v      # 18 concept query tests
python -m pytest tests/test_refresh.py -v    # 11 refresh proposal tests
python -m pytest tests/test_export.py -v     # 10 catalog export tests
python -m pytest tests/test_api.py -v        # 22 FastAPI endpoint tests
```

## Running a single test

```bash
python -m pytest tests/test_validate.py::TestInvalidData::test_invalid_data_exactly_six_violations -v
```

## What each test file covers

### test_validate.py -- SHACL governance controls

Verifies the core governance guarantee: valid data passes, invalid data fails
with exactly 6 violations covering every SHACL constraint type in the kit.

Expected output (excerpt):
```
TestValidData::test_valid_data_conforms PASSED
TestValidData::test_valid_data_has_expected_triple_count PASSED
TestInvalidData::test_invalid_data_does_not_conform PASSED
TestInvalidData::test_invalid_data_exactly_six_violations PASSED
TestInvalidData::test_invalid_status_not_in_allowed_values PASSED
TestInvalidData::test_metric_missing_calculation_logic PASSED
TestInvalidData::test_metric_missing_implementing_asset PASSED
TestInvalidData::test_data_asset_missing_steward PASSED
TestInvalidData::test_data_asset_missing_asset_type PASSED
TestInvalidData::test_review_cadence_not_positive PASSED
TestInvalidData::test_violations_target_expected_nodes PASSED
TestValidateCLI::test_cli_valid_returns_zero PASSED
TestValidateCLI::test_cli_invalid_returns_nonzero PASSED
```

The 6 violations tested are:

| Violation | Node | SHACL constraint |
|-----------|------|-----------------|
| Status "Candidate" not in allowed values | ChurnRiskTerm | sh:InConstraintComponent |
| Missing calculation logic | ChurnRiskTerm | sh:MinCountConstraintComponent |
| Missing implementing asset | ChurnRiskTerm | sh:MinCountConstraintComponent |
| Missing steward | UnownedCustomerExport | sh:MinCountConstraintComponent |
| Missing asset type | UnownedCustomerExport | sh:MinCountConstraintComponent |
| Review cadence = 0 (not positive) | ChurnRiskTerm | sh:MinInclusiveConstraintComponent |

### test_query.py -- SPARQL concept lookup

Tests the governed concept query that agents use at runtime. Each concept
(Customer, Active Customer, Net Revenue, Customer PII Policy) gets its own
test class verifying label, steward, definition, linked assets, and catalog ID.

Expected output (excerpt):
```
TestQueryCustomer::test_customer_returns_three_results PASSED
TestQueryNetRevenue::test_net_revenue_has_calculation_logic PASSED
TestQueryPIIPolicy::test_pii_policy_has_no_asset PASSED
TestQueryNotFound::test_nonexistent_returns_empty PASSED
```

### test_refresh.py -- Staleness detection

Tests the refresh flywheel with explicit date arithmetic. Verifies that:
- Active Customer (reviewed 2025-10-01, 90-day cadence) is overdue by 2026-06-05
- Customer, Net Revenue, and PII Policy are NOT overdue on that date
- Moving the as-of date forward catches more concepts
- PolicyConcept types are exempt from the missing-asset-link check

Expected output (excerpt):
```
TestOverdueDetection::test_active_customer_overdue_on_june_5 PASSED
TestOverdueDetection::test_customer_not_overdue_on_june_5 PASSED
TestDifferentAsOfDates::test_late_date_catches_all_concepts PASSED
TestMissingImplementationLink::test_policy_concepts_not_flagged PASSED
```

### test_export.py -- Catalog CSV generation

Tests that the glossary CSV export has the correct 10-column schema, contains
exactly 4 rows (all Approved concepts), and that individual rows have correct
content (synonyms, parent links, asset URIs).

Expected output (excerpt):
```
TestExportColumns::test_csv_has_correct_columns PASSED
TestExportRowCount::test_exports_four_approved_concepts PASSED
TestExportContent::test_customer_row_has_synonyms PASSED
TestExportCLI::test_cli_produces_csv PASSED
```

### test_api.py -- FastAPI context endpoint

Tests the `/concepts/{name}` REST endpoint using FastAPI's TestClient (no
server process needed). Covers successful lookups for all four concepts,
case-insensitive matching, and 404 responses for unknown concepts.

Expected output (excerpt):
```
TestGetNetRevenue::test_status_code_200 PASSED
TestGetNetRevenue::test_calculation_logic_present PASSED
TestGetCustomer::test_steward PASSED
TestCaseInsensitive::test_uppercase PASSED
TestNotFound::test_nonexistent_returns_404 PASSED
TestNotFound::test_404_has_detail_message PASSED
```

## Extending the tests

### Adding a new concept

1. Define it in `ontology/enterprise_ai.ttl` (SKOS + OWL type)
2. Add instance data in `data/sample_data_valid.ttl` (assets, use cases)
3. Add tests:

```python
# In test_query.py
class TestQueryNewConcept:
    def test_new_concept_returns_one_result(self, valid_graph):
        results = _query(valid_graph, "new concept")
        assert len(results) == 1

    def test_new_concept_steward(self, valid_graph):
        results = _query(valid_graph, "new concept")
        assert results[0]["steward"] == "Expected Steward"
```

4. Update the expected count in `test_export.py` if the concept is Approved
5. Add refresh date tests in `test_refresh.py` with the concept's review date

### Adding a new SHACL shape

1. Add the shape to `ontology/shapes.ttl`
2. Add deliberately invalid data to `data/sample_data_invalid.ttl`
3. Update `test_invalid_data_exactly_six_violations` with the new count
4. Add a test for the specific violation message:

```python
def test_new_violation(self, invalid_graph, shapes_graph):
    _, results_graph, _ = _validate(invalid_graph, shapes_graph)
    messages = _violation_messages(results_graph)
    assert "Your new SHACL message here." in messages
```

### Adding a new API endpoint

1. Add the route to `src/context_api.py`
2. Add a test class in `test_api.py`:

```python
class TestNewEndpoint:
    def test_returns_200(self, client):
        response = client.get("/new-endpoint")
        assert response.status_code == 200
```

## CI/CD integration

The GitHub Actions workflow (`.github/workflows/ontology-ci.yml`) runs the
full test suite on every push to `main` and every pull request that touches
`ontology/`, `data/`, `src/`, or `tests/`.

```yaml
test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.12'
    - run: pip install -r requirements.txt
    - name: Run test suite
      run: python -m pytest tests/ -v --tb=short
```

The CI has two jobs:

1. **validate** -- runs each script standalone (same as `make validate`, `make
   query`, etc.) to verify the kit works end-to-end
2. **test** -- runs `pytest` to verify all 75 assertions pass

Both must pass before a PR can merge.

## Test design principles

- **Independent**: Each test can run in isolation. Fixtures reload graphs
  fresh; CLI tests use temp directories.
- **Deterministic**: No random data, no network calls, no time-dependent
  behavior (dates are explicit parameters).
- **Two layers**: Each component has both in-process tests (fast, using
  fixtures) and CLI integration tests (via subprocess, verifying the script
  entry points).
- **Descriptive names**: Every test name says what it checks, so failures are
  self-documenting.
