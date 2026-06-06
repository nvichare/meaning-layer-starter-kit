# Test Suite -- The Meaning Layer Starter Kit

This directory contains the full pytest test suite for every component of the
starter kit. All 75 tests should pass on a fresh clone after installing
dependencies.

## Running the tests

```bash
# From the project root
python -m pytest tests/ -v
```

Or use the Makefile:

```bash
make test
```

## Test files

### tests/conftest.py -- Shared fixtures

Provides reusable graph fixtures so individual tests do not re-parse Turtle
files. Also sets the working directory to the project root for every test.

| Fixture          | What it loads                                          |
|------------------|-------------------------------------------------------|
| `ontology_graph` | `ontology/enterprise_ai.ttl` only                     |
| `valid_graph`    | Ontology + `data/sample_data_valid.ttl`                |
| `invalid_graph`  | Ontology + valid data + `data/sample_data_invalid.ttl` |
| `shapes_graph`   | `ontology/shapes.ttl` (SHACL controls)                 |

### tests/test_validate.py -- SHACL validation (13 tests)

| Test class       | Test                                           | What it verifies                                                    |
|------------------|------------------------------------------------|---------------------------------------------------------------------|
| TestValidData    | test_valid_data_conforms                       | Valid sample data passes SHACL validation                           |
| TestValidData    | test_valid_data_has_expected_triple_count       | Graph contains exactly 167 triples                                  |
| TestValidData    | test_valid_data_zero_violations                | No violation messages in the results graph                          |
| TestInvalidData  | test_invalid_data_does_not_conform             | Invalid data fails SHACL validation                                 |
| TestInvalidData  | test_invalid_data_exactly_six_violations       | Exactly 6 violations are reported                                   |
| TestInvalidData  | test_invalid_status_not_in_allowed_values      | ChurnRiskTerm status "Candidate" triggers InConstraint violation     |
| TestInvalidData  | test_metric_missing_calculation_logic          | ChurnRiskTerm missing calculationLogic triggers MinCount violation   |
| TestInvalidData  | test_metric_missing_implementing_asset         | ChurnRiskTerm missing implementedByAsset triggers MinCount violation |
| TestInvalidData  | test_data_asset_missing_steward                | UnownedCustomerExport missing steward triggers MinCount violation    |
| TestInvalidData  | test_data_asset_missing_asset_type             | UnownedCustomerExport missing assetType triggers MinCount violation  |
| TestInvalidData  | test_review_cadence_not_positive               | ChurnRiskTerm cadence=0 triggers MinInclusive violation             |
| TestInvalidData  | test_violations_target_expected_nodes          | Only ChurnRiskTerm and UnownedCustomerExport are violation targets   |
| TestValidateCLI  | test_cli_valid_returns_zero                    | validate_graph.py exits 0 for valid data                            |
| TestValidateCLI  | test_cli_invalid_returns_nonzero               | validate_graph.py exits 1 for invalid data                          |

### tests/test_query.py -- Concept querying (18 tests)

| Test class              | Test                                        | What it verifies                                       |
|-------------------------|---------------------------------------------|--------------------------------------------------------|
| TestQueryCustomer       | test_customer_returns_three_results         | "customer" matches Customer, Active Customer, PII      |
| TestQueryCustomer       | test_customer_labels                        | All three expected labels are present                  |
| TestQueryCustomer       | test_customer_term_has_correct_steward      | Customer steward is "Customer Data Council"            |
| TestQueryCustomer       | test_customer_term_links_to_master_table    | Customer links to CustomerMasterTable asset            |
| TestQueryActiveCustomer | test_active_customer_returns_one_result     | "active customer" matches exactly one concept          |
| TestQueryActiveCustomer | test_active_customer_definition             | Definition mentions "trailing 12 months"               |
| TestQueryActiveCustomer | test_active_customer_steward                | Steward is "Growth Analytics"                          |
| TestQueryNetRevenue     | test_net_revenue_returns_one_result         | "net revenue" matches exactly one concept              |
| TestQueryNetRevenue     | test_net_revenue_has_calculation_logic      | Calculation logic contains "SUM"                       |
| TestQueryNetRevenue     | test_net_revenue_links_to_revenue_mart      | Asset is RevenueMart with correct catalog ID           |
| TestQueryNetRevenue     | test_net_revenue_steward_is_finance         | Steward is "Finance Analytics"                         |
| TestQueryPIIPolicy      | test_pii_returns_one_result                 | "pii" matches exactly one concept                      |
| TestQueryPIIPolicy      | test_pii_policy_has_no_asset                | Policy concept has no implementing asset               |
| TestQueryPIIPolicy      | test_pii_policy_steward_is_privacy_office   | Steward is "Privacy Office"                            |
| TestQueryNotFound       | test_nonexistent_returns_empty              | "nonexistent" returns empty list                       |
| TestQueryNotFound       | test_gibberish_returns_empty                | Random string returns empty list                       |
| TestQueryCLI            | test_cli_revenue_returns_json               | CLI outputs valid JSON with Net Revenue                |
| TestQueryCLI            | test_cli_nonexistent_returns_empty_list     | CLI outputs [] for unknown term                        |

### tests/test_refresh.py -- Refresh proposals (11 tests)

| Test class                   | Test                                      | What it verifies                                       |
|------------------------------|-------------------------------------------|--------------------------------------------------------|
| TestOverdueDetection         | test_active_customer_overdue_on_june_5    | Active Customer (reviewed 2025-10-01, 90d) is overdue  |
| TestOverdueDetection         | test_customer_not_overdue_on_june_5       | Customer (reviewed 2026-05-20, 90d) is current         |
| TestOverdueDetection         | test_net_revenue_not_overdue_on_june_5    | Net Revenue (reviewed 2026-04-15, 60d) is current      |
| TestOverdueDetection         | test_pii_policy_not_overdue_on_june_5     | PII Policy (reviewed 2026-05-30, 30d) is current       |
| TestNoOverdue                | test_no_overdue_early_date                | No concepts overdue as of 2025-10-02                   |
| TestDifferentAsOfDates       | test_late_date_catches_all_concepts       | All 4 concepts overdue by 2027-01-01                   |
| TestDifferentAsOfDates       | test_mid_date_catches_some_concepts       | Active Customer + Net Revenue overdue by 2026-06-15    |
| TestMissingImplementationLink| test_policy_concepts_not_flagged          | PolicyConcept types are exempt from asset link check    |
| TestMissingImplementationLink| test_linked_concepts_not_flagged          | Concepts with implementedByAsset are not flagged       |
| TestRefreshCLI               | test_cli_produces_output_file             | CLI writes valid JSON proposals file                   |
| TestRefreshCLI               | test_cli_early_date_zero_proposals        | CLI reports 0 proposals for early date                 |

### tests/test_export.py -- Catalog export (10 tests)

| Test class        | Test                                   | What it verifies                                  |
|-------------------|----------------------------------------|---------------------------------------------------|
| TestExportColumns | test_csv_has_correct_columns           | CSV has all 10 expected column headers            |
| TestExportRowCount| test_exports_four_approved_concepts    | Exactly 4 approved concepts are exported          |
| TestExportRowCount| test_rows_sorted_by_name               | Rows are alphabetically sorted by name            |
| TestExportContent | test_customer_row_has_synonyms         | Customer row contains "Buyer" and "Client"        |
| TestExportContent | test_active_customer_has_parent        | Active Customer parent_term_uri is CustomerTerm   |
| TestExportContent | test_net_revenue_linked_to_asset       | Net Revenue links to RevenueMart                  |
| TestExportContent | test_pii_policy_has_no_linked_asset    | PII Policy has empty linked_asset_uris            |
| TestExportContent | test_all_rows_have_status_approved     | Every exported row has status Approved/Deprecated |
| TestExportCLI     | test_cli_produces_csv                  | CLI writes CSV with 4 rows and correct headers    |
| TestExportCLI     | test_cli_output_message                | CLI prints "Exported 4 catalog-ready..."          |

### tests/test_api.py -- FastAPI context endpoint (22 tests)

| Test class          | Test                                  | What it verifies                                  |
|---------------------|---------------------------------------|---------------------------------------------------|
| TestGetNetRevenue   | test_status_code_200                  | GET /concepts/net revenue returns 200             |
| TestGetNetRevenue   | test_label                            | Response label is "Net Revenue"                   |
| TestGetNetRevenue   | test_definition_present               | Definition mentions "gross revenue"               |
| TestGetNetRevenue   | test_calculation_logic_present        | Calculation logic contains "SUM"                  |
| TestGetNetRevenue   | test_steward                          | Steward is "Finance Analytics"                    |
| TestGetNetRevenue   | test_status_approved                  | Status is "Approved"                              |
| TestGetNetRevenue   | test_has_implementing_asset           | Has asset with RevenueMart URI and catalog ID     |
| TestGetCustomer     | test_status_code_200                  | GET /concepts/customer returns 200                |
| TestGetCustomer     | test_label                            | Response label is "Customer"                      |
| TestGetCustomer     | test_steward                          | Steward is "Customer Data Council"                |
| TestGetCustomer     | test_has_implementing_asset           | Has at least one implementing asset               |
| TestGetCustomer     | test_review_cadence                   | Review cadence is 90 days                         |
| TestGetActiveCustomer | test_status_code_200                | GET /concepts/active customer returns 200         |
| TestGetActiveCustomer | test_label                          | Response label is "Active Customer"               |
| TestGetPIIPolicy    | test_status_code_200                  | GET /concepts/customer pii policy returns 200     |
| TestGetPIIPolicy    | test_no_implementing_assets           | Policy has no implementing assets                 |
| TestCaseInsensitive | test_uppercase                        | "NET REVENUE" matches                             |
| TestCaseInsensitive | test_mixed_case                       | "Net Revenue" matches                             |
| TestCaseInsensitive | test_lowercase                        | "net revenue" matches                             |
| TestNotFound        | test_nonexistent_returns_404          | Unknown concept returns 404                       |
| TestNotFound        | test_404_has_detail_message           | 404 body contains "not found"                     |
| TestNotFound        | test_empty_name_returns_404           | Random string returns 404                         |

## Expected output

```
$ python -m pytest tests/ -v
======================== test session starts ========================
tests/test_api.py::TestGetNetRevenue::test_status_code_200 PASSED
tests/test_api.py::TestGetNetRevenue::test_label PASSED
tests/test_api.py::TestGetNetRevenue::test_definition_present PASSED
tests/test_api.py::TestGetNetRevenue::test_calculation_logic_present PASSED
tests/test_api.py::TestGetNetRevenue::test_steward PASSED
tests/test_api.py::TestGetNetRevenue::test_status_approved PASSED
tests/test_api.py::TestGetNetRevenue::test_has_implementing_asset PASSED
tests/test_api.py::TestGetCustomer::test_status_code_200 PASSED
tests/test_api.py::TestGetCustomer::test_label PASSED
tests/test_api.py::TestGetCustomer::test_steward PASSED
tests/test_api.py::TestGetCustomer::test_has_implementing_asset PASSED
tests/test_api.py::TestGetCustomer::test_review_cadence PASSED
tests/test_api.py::TestGetActiveCustomer::test_status_code_200 PASSED
tests/test_api.py::TestGetActiveCustomer::test_label PASSED
tests/test_api.py::TestGetPIIPolicy::test_status_code_200 PASSED
tests/test_api.py::TestGetPIIPolicy::test_no_implementing_assets PASSED
tests/test_api.py::TestCaseInsensitive::test_uppercase PASSED
tests/test_api.py::TestCaseInsensitive::test_mixed_case PASSED
tests/test_api.py::TestCaseInsensitive::test_lowercase PASSED
tests/test_api.py::TestNotFound::test_nonexistent_returns_404 PASSED
tests/test_api.py::TestNotFound::test_404_has_detail_message PASSED
tests/test_api.py::TestNotFound::test_empty_name_returns_404 PASSED
tests/test_export.py::TestExportColumns::test_csv_has_correct_columns PASSED
tests/test_export.py::TestExportRowCount::test_exports_four_approved_concepts PASSED
tests/test_export.py::TestExportRowCount::test_rows_sorted_by_name PASSED
tests/test_export.py::TestExportContent::test_customer_row_has_synonyms PASSED
tests/test_export.py::TestExportContent::test_active_customer_has_parent PASSED
tests/test_export.py::TestExportContent::test_net_revenue_linked_to_asset PASSED
tests/test_export.py::TestExportContent::test_pii_policy_has_no_linked_asset PASSED
tests/test_export.py::TestExportContent::test_all_rows_have_status_approved PASSED
tests/test_export.py::TestExportCLI::test_cli_produces_csv PASSED
tests/test_export.py::TestExportCLI::test_cli_output_message PASSED
tests/test_query.py::TestQueryCustomer::test_customer_returns_three_results PASSED
tests/test_query.py::TestQueryCustomer::test_customer_labels PASSED
tests/test_query.py::TestQueryCustomer::test_customer_term_has_correct_steward PASSED
tests/test_query.py::TestQueryCustomer::test_customer_term_links_to_master_table PASSED
tests/test_query.py::TestQueryActiveCustomer::test_active_customer_returns_one_result PASSED
tests/test_query.py::TestQueryActiveCustomer::test_active_customer_definition PASSED
tests/test_query.py::TestQueryActiveCustomer::test_active_customer_steward PASSED
tests/test_query.py::TestQueryNetRevenue::test_net_revenue_returns_one_result PASSED
tests/test_query.py::TestQueryNetRevenue::test_net_revenue_has_calculation_logic PASSED
tests/test_query.py::TestQueryNetRevenue::test_net_revenue_links_to_revenue_mart PASSED
tests/test_query.py::TestQueryNetRevenue::test_net_revenue_steward_is_finance PASSED
tests/test_query.py::TestQueryPIIPolicy::test_pii_returns_one_result PASSED
tests/test_query.py::TestQueryPIIPolicy::test_pii_policy_has_no_asset PASSED
tests/test_query.py::TestQueryPIIPolicy::test_pii_policy_steward_is_privacy_office PASSED
tests/test_query.py::TestQueryNotFound::test_nonexistent_returns_empty PASSED
tests/test_query.py::TestQueryNotFound::test_gibberish_returns_empty PASSED
tests/test_query.py::TestQueryCLI::test_cli_revenue_returns_json PASSED
tests/test_query.py::TestQueryCLI::test_cli_nonexistent_returns_empty_list PASSED
tests/test_refresh.py::TestOverdueDetection::test_active_customer_overdue_on_june_5 PASSED
tests/test_refresh.py::TestOverdueDetection::test_customer_not_overdue_on_june_5 PASSED
tests/test_refresh.py::TestOverdueDetection::test_net_revenue_not_overdue_on_june_5 PASSED
tests/test_refresh.py::TestOverdueDetection::test_pii_policy_not_overdue_on_june_5 PASSED
tests/test_refresh.py::TestNoOverdue::test_no_overdue_early_date PASSED
tests/test_refresh.py::TestDifferentAsOfDates::test_late_date_catches_all_concepts PASSED
tests/test_refresh.py::TestDifferentAsOfDates::test_mid_date_catches_some_concepts PASSED
tests/test_refresh.py::TestMissingImplementationLink::test_policy_concepts_not_flagged PASSED
tests/test_refresh.py::TestMissingImplementationLink::test_linked_concepts_not_flagged PASSED
tests/test_refresh.py::TestRefreshCLI::test_cli_produces_output_file PASSED
tests/test_refresh.py::TestRefreshCLI::test_cli_early_date_zero_proposals PASSED
tests/test_validate.py::TestValidData::test_valid_data_conforms PASSED
tests/test_validate.py::TestValidData::test_valid_data_has_expected_triple_count PASSED
tests/test_validate.py::TestValidData::test_valid_data_zero_violations PASSED
tests/test_validate.py::TestInvalidData::test_invalid_data_does_not_conform PASSED
tests/test_validate.py::TestInvalidData::test_invalid_data_exactly_six_violations PASSED
tests/test_validate.py::TestInvalidData::test_invalid_status_not_in_allowed_values PASSED
tests/test_validate.py::TestInvalidData::test_metric_missing_calculation_logic PASSED
tests/test_validate.py::TestInvalidData::test_metric_missing_implementing_asset PASSED
tests/test_validate.py::TestInvalidData::test_data_asset_missing_steward PASSED
tests/test_validate.py::TestInvalidData::test_data_asset_missing_asset_type PASSED
tests/test_validate.py::TestInvalidData::test_review_cadence_not_positive PASSED
tests/test_validate.py::TestInvalidData::test_violations_target_expected_nodes PASSED
tests/test_validate.py::TestValidateCLI::test_cli_valid_returns_zero PASSED
tests/test_validate.py::TestValidateCLI::test_cli_invalid_returns_nonzero PASSED
====================== 75 passed in 4s ======================
```

## Adding new tests

When you extend the ontology with new concepts:

1. Add the concept to `ontology/enterprise_ai.ttl`
2. Add instance data to `data/sample_data_valid.ttl`
3. Add test cases for the new concept in the relevant test file:
   - If it should pass validation: add an assertion in `test_validate.py`
   - If it should be queryable: add a test class in `test_query.py`
   - If it has review dates: add date-based checks in `test_refresh.py`
   - If it should be exported: add content checks in `test_export.py`
   - If the API should return it: add a test class in `test_api.py`

When you add new SHACL shapes:

1. Add the shape to `ontology/shapes.ttl`
2. Create matching invalid data in `data/sample_data_invalid.ttl`
3. Update the expected violation count in `test_invalid_data_exactly_six_violations`
4. Add a test for the specific violation message

When you add new scripts:

1. Create `tests/test_<script_name>.py`
2. Add both in-process tests (using fixtures) and CLI integration tests (using subprocess)
3. Update this README with the new test inventory
