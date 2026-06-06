<p align="center">
  <strong>Meaning Layer Starter Kit</strong>
</p>

<p align="center">
  Build your first governed enterprise ontology in an afternoon.
</p>

<p align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python 3.10+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License"></a>
  <a href="https://github.com/nvichare/meaning-layer-starter-kit/actions"><img src="https://img.shields.io/badge/CI-passing-brightgreen?logo=githubactions&logoColor=white" alt="Tests Passing"></a>
  <a href="https://github.com/nvichare/meaning-layer-starter-kit/stargazers"><img src="https://img.shields.io/github/stars/nvichare/meaning-layer-starter-kit?style=flat&logo=github" alt="GitHub Stars"></a>
</p>

<p align="center">
  Companion repository for <em><a href="https://amazon.com">The Meaning Layer: Who Governs the AI That Defines Your Data</a></em> by Nidhi Vichare.
</p>

---

An executable reference implementation of an **enterprise AI meaning layer** -- the governed semantic layer that sits between your data catalog and your AI agents. It ships a SKOS+OWL ontology, SHACL validation controls, a SPARQL-backed context API, catalog sync adapters, and a refresh flywheel -- all runnable with `make` and testable in CI. Small enough to read in an afternoon, complete enough to fork and extend for production.

## Table of Contents

- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [What's Inside](#whats-inside)
- [Usage Examples](#usage-examples)
- [Testing](#testing)
- [Customizing for Your Domain](#customizing-for-your-domain)
- [Connecting to Your Catalog](#connecting-to-your-catalog)
- [Exposing to Agents](#exposing-to-agents)
- [The Governance Loop](#the-governance-loop)
- [From the Book](#from-the-book)
- [Contributing](#contributing)
- [License](#license)

## Quick Start

Five commands from zero to a validated, queryable meaning layer:

```bash
git clone https://github.com/nvichare/meaning-layer-starter-kit.git
cd meaning-layer-starter-kit
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
make validate query refresh export
```

You should see governed data validated against SHACL shapes, a concept lookup for "Net Revenue," a refresh proposal for stale concepts, and a catalog-ready CSV export -- all in under five seconds.

## Architecture

```
                         The Meaning Layer Stack
  ┌──────────────────────────────────────────────────────────────┐
  │                                                              │
  │   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
  │   │  SKOS + OWL  │    │    SHACL     │    │   Refresh    │   │
  │   │  Ontology    │───▶│  Validation  │    │   Flywheel   │   │
  │   │              │    │  Controls    │    │              │   │
  │   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘   │
  │          │                   │                   │           │
  │          ▼                   ▼                   ▼           │
  │   ┌──────────────────────────────────────────────────────┐   │
  │   │              SPARQL Query Runtime                    │   │
  │   │         (rdflib graph + context queries)             │   │
  │   └──────────────────────┬───────────────────────────────┘   │
  │                          │                                   │
  │            ┌─────────────┼─────────────┐                     │
  │            ▼             ▼             ▼                     │
  │   ┌──────────────┐ ┌──────────┐ ┌──────────────┐            │
  │   │  Context API │ │ Catalog  │ │   Glossary   │            │
  │   │  (FastAPI)   │ │  Sync    │ │   Export     │            │
  │   │              │ │ Adapters │ │   (CSV)      │            │
  │   └──────┬───────┘ └────┬─────┘ └──────────────┘            │
  │          │              │                                    │
  │          ▼              ▼                                    │
  │   ┌────────────┐  ┌─────────────────────┐                   │
  │   │ AI Agents  │  │ Atlan / OpenMetadata │                  │
  │   │ (MCP/RAG)  │  │ / Alation            │                  │
  │   └────────────┘  └─────────────────────┘                   │
  │                                                              │
  └──────────────────────────────────────────────────────────────┘
```

| Layer | Purpose | This kit provides |
|-------|---------|-------------------|
| **Business vocabulary** | Definitions, synonyms, ownership | `enterprise_ai.ttl` (SKOS concepts) |
| **Formal ontology** | Stable identifiers, relationships | `enterprise_ai.ttl` (OWL classes + properties) |
| **Validation controls** | Prevent bad meaning from publishing | `shapes.ttl` (SHACL shapes) |
| **Query runtime** | Query approved meaning at runtime | `query_context.py` + `context_api.py` |
| **Catalog sync** | Push governed terms to your catalog | `sync_openmetadata.py` + `sync_atlan.py` |
| **AI context service** | Supply meaning to agents before they act | `context_api.py` (FastAPI) |
| **Refresh flywheel** | Keep meaning current, detect drift | `propose_refresh.py` |

## What's Inside

```
meaning-layer-starter-kit/
│
├── ontology/                          # The governed knowledge model
│   ├── enterprise_ai.ttl              # SKOS + OWL reference ontology
│   │                                  #   4 business concepts, 7 relationships,
│   │                                  #   3 data assets, 2 AI use cases
│   └── shapes.ttl                     # SHACL governance controls
│                                      #   GovernedConceptShape: label, definition,
│                                      #     steward, status, review date, cadence
│                                      #   MetricConceptShape: calculation logic,
│                                      #     implementing asset required
│                                      #   DataAssetShape: source system, type, steward
│
├── data/                              # Instance data for validation
│   ├── sample_data_valid.ttl          # 167 triples of governed enterprise data
│   │                                  #   3 data assets, 2 AI use cases, catalog IDs
│   └── sample_data_invalid.ttl        # Deliberately broken data (6 violations)
│                                      #   Missing steward, missing asset type,
│                                      #   invalid status, zero cadence, no calc logic
│
├── src/                               # Executable meaning layer components
│   ├── validate_graph.py              # SHACL validation against governance shapes
│   ├── query_context.py               # SPARQL concept lookup by label fragment
│   ├── propose_refresh.py             # Detect stale concepts, generate proposals
│   ├── export_catalog_glossary.py     # Export approved terms to catalog-ready CSV
│   ├── sync_openmetadata.py           # OpenMetadata glossary term adapter (dry-run)
│   ├── sync_atlan.py                  # Atlan Business Graph import CSV generator
│   └── context_api.py                 # FastAPI endpoint for agent context lookups
│
├── config/
│   └── refresh_policy.yaml            # Review cadences, proposal sources,
│                                      #   release controls (SHACL + steward + lineage)
│
├── catalog_sync/                      # Generated catalog artifacts
│   ├── glossary_terms.csv             # Exported glossary (auto-generated by export)
│   └── atlan_business_graph_import.csv  # Atlan import template (auto-generated)
│
├── docs/                              # Practitioner guide and reference outputs
│   ├── enterprise_ai_ontology_practitioner_guide.pdf  # 23-page implementation guide
│   ├── competency_questions_template.csv   # Scope your ontology with CQs
│   ├── concept_backlog_template.csv        # Track concept development lifecycle
│   ├── vendor_options_scorecard.csv        # Evaluate catalog/ontology tooling
│   ├── ontology.dot                        # Graphviz source for concept graph
│   └── (recorded outputs)                  # validation, query, refresh, export outputs
│
├── .github/workflows/
│   └── ontology-ci.yml                # CI pipeline: validate + query + refresh + export
│                                      #   on every push to main and every PR
│
├── tests/                             # Full pytest test suite (75 tests)
│   ├── conftest.py                    # Shared fixtures (graph loading, cwd setup)
│   ├── test_validate.py               # 13 SHACL validation tests
│   ├── test_query.py                  # 18 concept query tests
│   ├── test_refresh.py                # 11 refresh proposal tests
│   ├── test_export.py                 # 10 catalog export tests
│   ├── test_api.py                    # 22 FastAPI endpoint tests
│   └── README.md                      # Test inventory and extension guide
│
├── Makefile                           # All commands: validate, query, refresh, export,
│                                      #   sync-openmetadata, sync-atlan, api, test, all
├── requirements.txt                   # rdflib, pyshacl, PyYAML, requests, fastapi,
│                                      #   uvicorn, pytest, httpx
├── TESTING.md                         # Comprehensive testing guide
└── LICENSE                            # MIT
```

## Usage Examples

Every command is a `make` target. Here is what each one does and what you will see.

### Validate governed data (good data)

```bash
make validate
```

```
SHACL conforms: True
Triples validated: 167
All ontology governance controls passed.
```

All 167 triples pass all SHACL constraints: every concept has a label, definition, steward, valid lifecycle status, review date, and positive review cadence. Metrics have calculation logic and implementing assets. Data assets have source systems, types, and stewards.

### Validate governed data (deliberately broken data)

```bash
make validate-invalid
```

```
SHACL conforms: False
Triples validated: 177

Validation report
-----------------
Validation Report
Conforms: False
Results (6):
Constraint Violation in InConstraintComponent:
    Focus Node: ex:ChurnRiskTerm
    Value Node: Literal("Candidate")
    Message: Lifecycle status must be Draft, Approved, or Deprecated.

Constraint Violation in MinCountConstraintComponent:
    Focus Node: ex:ChurnRiskTerm
    Message: A governed metric must link to at least one implementing data asset.

Constraint Violation in MinCountConstraintComponent:
    Focus Node: ex:ChurnRiskTerm
    Message: A governed metric requires deterministic calculation logic.

Constraint Violation in MinCountConstraintComponent:
    Focus Node: ex:UnownedCustomerExport
    Message: Each data asset requires an accountable owner or steward.

Constraint Violation in MinCountConstraintComponent:
    Focus Node: ex:UnownedCustomerExport
    Message: Each data asset requires an asset type.

Constraint Violation in MinInclusiveConstraintComponent:
    Focus Node: ex:ChurnRiskTerm
    Value Node: Literal("0")
    Message: Every governed concept requires a positive review cadence.

Wrote validation-report.ttl
```

Six violations caught by the semantic canaries: an invalid lifecycle status ("Candidate" is not in the allowed set), a metric missing its calculation logic and implementing asset, a data asset with no steward or type, and a zero review cadence. This is exactly what SHACL controls are designed to prevent in production.

### Query governed context

```bash
make query
```

```json
[
  {
    "concept_uri": "https://example.com/enterprise-ai/NetRevenueTerm",
    "label": "Net Revenue",
    "definition": "Recognized gross revenue less contractual discounts, returns, credits, and rebates.",
    "steward": "Finance Analytics",
    "status": "Approved",
    "calculation_logic": "SUM(gross_revenue - discounts - returns - credits - rebates)",
    "asset_uri": "https://example.com/enterprise-ai/RevenueMart",
    "catalog_id": "snowflake.finance.revenue_mart"
  }
]
```

Ask the meaning layer "what does revenue mean?" and get back the governed definition, the owning steward, the deterministic calculation logic, the implementing data asset, and its catalog identifier. This is the context an AI agent needs before it writes a SQL query or answers a finance question.

### Detect stale concepts and propose refreshes

```bash
make refresh
```

```
Generated 1 refresh proposal(s) as of 2026-06-05.
1. [REVIEW_OVERDUE] Active Customer: Assign steward review task and run lineage
   impact analysis before republishing.
Wrote refresh-proposals.json
```

The refresh flywheel compares each concept's `lastReviewedAt` date plus its `reviewCadenceDays` against today. "Active Customer" was last reviewed on 2025-10-01 with a 90-day cadence -- it is overdue. The proposal recommends a steward review and lineage impact analysis.

### Export catalog-ready glossary

```bash
make export
```

```
Exported 4 catalog-ready glossary terms to catalog_sync/glossary_terms.csv
```

Generates a CSV with term URIs, names, definitions, synonyms, parent terms, stewards, lifecycle statuses, review dates, cadences, and linked asset URIs -- ready to load into any catalog that accepts CSV import.

### Sync to Atlan

```bash
make sync-atlan
```

```
Prepared 4 Atlan Business Graph import row(s) at catalog_sync/atlan_business_graph_import.csv
```

Transforms the glossary CSV into Atlan's Business Graph import format.

### Sync to OpenMetadata (dry-run)

```bash
make sync-openmetadata
```

Outputs JSON payloads matching the OpenMetadata `/v1/glossaryTerms` API schema. Default is dry-run; add `--apply` with credentials to push live.

### Start the agent context API

```bash
make api
```

Starts a FastAPI server at `http://localhost:8000`. Query any concept by name:

```bash
curl http://localhost:8000/concepts/Net%20Revenue
```

```json
{
  "uri": "https://example.com/enterprise-ai/NetRevenueTerm",
  "label": "Net Revenue",
  "definition": "Recognized gross revenue less contractual discounts, returns, credits, and rebates.",
  "status": "Approved",
  "steward": "Finance Analytics",
  "calculation_logic": "SUM(gross_revenue - discounts - returns - credits - rebates)",
  "last_reviewed_at": "2026-04-15",
  "review_cadence_days": "60",
  "implemented_by_assets": [
    {
      "uri": "https://example.com/enterprise-ai/RevenueMart",
      "catalog_id": "snowflake.finance.revenue_mart",
      "source_system": "Snowflake.FINANCE",
      "asset_type": "Table"
    }
  ]
}
```

Interactive docs available at `http://localhost:8000/docs` (Swagger UI).

## Testing

### Run the pytest suite

```bash
make test     # or: python -m pytest tests/ -v
```

The kit includes **75 tests** across five test files. All pass in approximately 4 seconds:

```
tests/test_validate.py    13 tests   SHACL pass/fail, all 6 violation types, CLI exit codes
tests/test_query.py       18 tests   Every concept queried, field checks, not-found cases
tests/test_refresh.py     11 tests   Overdue detection, date math, missing-link detection
tests/test_export.py      10 tests   CSV columns, row count, content, CLI output
tests/test_api.py         22 tests   REST endpoint for all concepts, case insensitivity, 404
```

For the full test inventory with every test name and what it verifies, see [TESTING.md](TESTING.md) and [tests/README.md](tests/README.md).

### Run the full validation suite

```bash
make validate              # Should exit 0 (all governance controls pass)
make validate-invalid      # Should exit 1 (6 violations detected)
```

### Run everything at once

```bash
make all      # validate + query + refresh + export + test
```

### CI pipeline

Every push to `main` and every pull request runs the full suite automatically via GitHub Actions (`.github/workflows/ontology-ci.yml`):

1. **validate** job -- runs each script standalone (`validate`, `query`, `refresh`, `export`)
2. **test** job -- runs `python -m pytest tests/ -v --tb=short` (all 75 tests)

Both jobs must pass before a PR can merge.

### Adding your own tests

1. **Add a new SHACL shape** in `ontology/shapes.ttl` to enforce a new constraint
2. **Add valid triples** in `data/sample_data_valid.ttl` that satisfy it
3. **Add invalid triples** in `data/sample_data_invalid.ttl` that violate it
4. **Add pytest assertions** in the relevant test file (see [TESTING.md](TESTING.md) for examples)
5. **Run `make validate` and `make test`** to confirm everything passes
6. The CI pipeline picks up changes automatically -- no test configuration needed

### Competency questions

Use `docs/competency_questions_template.csv` to define the questions your ontology must answer. Each row links a business question to the concept, relationship, or asset that should resolve it. This is the semantic equivalent of a test specification.

## Customizing for Your Domain

The starter kit ships with a financial services example (Customer, Active Customer, Net Revenue, Customer PII Policy). Here is how to replace it with your domain.

### Step 1: Define your concepts

Edit `ontology/enterprise_ai.ttl`. Replace the example concepts with your own:

```turtle
ex:YourConceptTerm a skos:Concept, ex:MetricConcept ;
  skos:inScheme ex:EnterpriseBusinessVocabulary ;
  skos:prefLabel "Your Concept"@en ;
  skos:definition "Your precise business definition."@en ;
  ex:calculationLogic "Your deterministic formula" ;
  ex:steward "Your Steward Team" ;
  ex:status "Draft" ;
  ex:lastReviewedAt "2026-06-01"^^xsd:date ;
  ex:reviewCadenceDays 90 ;
  ex:implementedByAsset ex:YourDataAsset .
```

Choose the right concept type: `EntityConcept` for things (Customer, Product), `MetricConcept` for measures (Revenue, Churn Rate), `PolicyConcept` for rules (PII Policy), `ProcessConcept` for workflows.

### Step 2: Add SHACL shapes for your constraints

If your domain needs additional validation rules, add shapes in `ontology/shapes.ttl`:

```turtle
ex:YourDomainShape a sh:NodeShape ;
  sh:targetClass ex:YourConceptType ;
  sh:property [
    sh:path ex:yourRequiredProperty ;
    sh:minCount 1 ;
    sh:message "Your validation message." ;
  ] .
```

### Step 3: Add instance data

Create data assets in `data/sample_data_valid.ttl`:

```turtle
ex:YourDataAsset a ex:DataAsset ;
  ex:sourceSystem "Your.SourceSystem" ;
  ex:assetType "Table" ;
  ex:steward "Your Data Team" ;
  ex:catalogId "your.catalog.identifier" .
```

### Step 4: Validate

```bash
make validate
```

If it passes, your governed concepts satisfy all SHACL constraints. If it fails, the validation report tells you exactly which constraint was violated and on which node.

### Step 5: Configure refresh policy

Edit `config/refresh_policy.yaml` to set review cadences for your domain:

```yaml
review_policy:
  default_cadence_days: 90
  critical_metrics_cadence_days: 30
  privacy_policy_cadence_days: 30
```

## Connecting to Your Catalog

The starter kit includes adapters for three major data catalogs. All default to dry-run mode -- no credentials required to preview the output.

### Atlan

```bash
make sync-atlan
```

Generates `catalog_sync/atlan_business_graph_import.csv` with columns matching Atlan's Business Graph import template: Glossary, Term, Definition, Synonyms, Status, Steward, Ontology URI, and Linked Assets.

**To load into Atlan:**
1. Review the generated CSV
2. Use Atlan's Asset Import for glossaries, or
3. Translate the rows into `pyatlan` `AtlasGlossaryTerm` creator calls

### OpenMetadata

```bash
make sync-openmetadata
```

Generates JSON payloads matching the OpenMetadata `/v1/glossaryTerms` API. Each payload includes `name`, `displayName`, `description`, `glossary`, `synonyms`, `references` (ontology URI), and `extension` fields for steward, review date, and cadence.

**To push live:**
```bash
export OPENMETADATA_BASE_URL=https://your-tenant.openmetadata.example/api
export OPENMETADATA_TOKEN=your-jwt-token
python src/sync_openmetadata.py --apply
```

### Alation

The exported `catalog_sync/glossary_terms.csv` is compatible with Alation's glossary import. Map columns as follows:

| Starter Kit CSV Column | Alation Field |
|------------------------|---------------|
| `name` | Title |
| `definition` | Description |
| `synonyms` | Synonyms (pipe-delimited) |
| `steward` | Steward |
| `status` | Status |

### Before going to production

Review the checklist in `docs/README.md`:

1. Validate dry-run payloads against your tenant's API version
2. Add authentication, authorization, and retries
3. Add audit logging and idempotency controls
4. Publish only from approved ontology releases
5. Use `docs/vendor_options_scorecard.csv` to evaluate tooling options

## Exposing to Agents

The meaning layer exists so that AI agents consult governed definitions before they act. Here are three patterns.

### Pattern 1: Context API (included)

Start the FastAPI server and point your agent to it:

```bash
make api
# Agent calls: GET /concepts/{concept_name}
```

The agent receives the governed definition, calculation logic, steward, lifecycle status, implementing assets, and catalog identifiers. It can use this context to write correct SQL, answer questions accurately, or refuse to act on deprecated concepts.

### Pattern 2: MCP (Model Context Protocol)

Wrap the context API as an MCP tool so LLM agents discover it automatically:

```python
# Example MCP tool definition
{
    "name": "lookup_governed_concept",
    "description": "Look up the governed business definition, calculation logic, and steward for a concept before using it in queries or answers.",
    "parameters": {
        "concept_name": {
            "type": "string",
            "description": "The business concept to look up, e.g. 'Net Revenue'"
        }
    }
}
```

The agent calls `lookup_governed_concept("Net Revenue")` and receives the same governed context as the REST API.

### Pattern 3: RAG grounding

Export the glossary CSV and index it in your vector store alongside your documents. When the RAG pipeline retrieves context for a finance question, it pulls the governed definition of "Net Revenue" -- not a stale wiki page or a Slack message from 2023.

### What agents get

Regardless of pattern, the agent receives:

| Field | Why it matters |
|-------|----------------|
| `definition` | The one approved meaning -- no ambiguity |
| `calculation_logic` | Deterministic formula the agent must use |
| `status` | Agent should refuse to use Deprecated concepts |
| `steward` | Who to escalate to when uncertain |
| `catalog_id` | Exact table/view to query |
| `last_reviewed_at` | Agent can warn users about stale definitions |

## The Governance Loop

The meaning layer is not a one-time build. It is a continuous loop that keeps meaning current as the business evolves.

```
    ┌──────────┐
    │ OBSERVE  │  Schema drift, lineage changes, agent low-confidence
    └────┬─────┘  answers, data quality incidents, catalog search misses
         │
         ▼
    ┌──────────┐
    │ PROPOSE  │  propose_refresh.py generates change proposals
    └────┬─────┘  (REVIEW_OVERDUE, MISSING_IMPLEMENTATION_LINK)
         │
         ▼
    ┌──────────┐
    │ VALIDATE │  SHACL shapes catch invalid changes before they merge
    └────┬─────┘  (CI runs on every PR -- ontology-ci.yml)
         │
         ▼
    ┌──────────┐
    │ RATIFY   │  Steward reviews and approves via pull request
    └────┬─────┘  (status: Draft -> Approved, lastReviewedAt updated)
         │
         ▼
    ┌──────────┐
    │ VERSION  │  Ontology changes are committed to Git
    └────┬─────┘  (Turtle files are diffable, reviewable, branchable)
         │
         ▼
    ┌──────────┐
    │ PUBLISH  │  Export to catalog, update context API, notify agents
    └────┬─────┘  (make export, make sync-atlan, make sync-openmetadata)
         │
         └────────────────▶ back to OBSERVE
```

The `config/refresh_policy.yaml` defines what triggers proposals:

```yaml
proposal_sources:
  - schema_drift                  # Upstream schema changed
  - lineage_change                # Lineage graph was rewired
  - steward_review_due            # Review cadence expired
  - catalog_search_no_result      # Users searched but found nothing
  - agent_low_confidence_answer   # Agent was uncertain
  - data_quality_incident         # DQ alert fired
```

And what controls gate a release:

```yaml
release_controls:
  require_shacl_validation: true          # Must pass all shapes
  require_steward_approval: true          # Steward must approve
  require_lineage_impact_analysis: true   # Check downstream impact
  deprecate_instead_of_delete: true       # Never delete, only deprecate
```

## From the Book

This starter kit is the companion code for *The Meaning Layer: Who Governs the AI That Defines Your Data* by Nidhi Vichare.

> "The enterprise that owns its meaning owns its future. The rest are turning the wheel and hoping."

The book covers:

- Why every AI initiative eventually hits a meaning problem
- How semantic layers differ from (and complement) data catalogs
- The organizational design for ontology governance -- who decides what "Customer" means
- SKOS, SHACL, and OWL: when to use each, and when not to
- Patterns for wiring governed meaning into LLM agents, copilots, and RAG pipelines
- The refresh flywheel: keeping meaning current without drowning in process

The 23-page practitioner guide included in `docs/enterprise_ai_ontology_practitioner_guide.pdf` provides step-by-step implementation guidance.

*The Meaning Layer* is available on [Amazon Kindle](https://amazon.com).

## Contributing

Contributions are welcome. Here is how to get started:

1. **Fork** the repository
2. **Create a feature branch** (`git checkout -b add-supply-chain-concepts`)
3. **Make your changes** -- add concepts, shapes, adapters, or documentation
4. **Run validation** (`make validate`) -- all SHACL controls must pass
5. **Open a pull request** with a clear description of what changed and why

### Good first contributions

- Add a new business concept to the ontology (with SHACL-compliant metadata)
- Add a SHACL shape for a domain-specific constraint
- Add a catalog sync adapter for a new platform
- Add competency questions to `docs/competency_questions_template.csv`
- Improve the practitioner guide

### Code style

- Turtle files: use the prefix conventions established in `enterprise_ai.ttl`
- Python files: standard library style, type hints, docstrings
- Every concept must pass `make validate` before merge

## License

MIT License. See [LICENSE](LICENSE).

---

<p align="center">
  Built with governed meaning. Validated by semantic canaries.<br>
  <a href="https://amazon.com"><em>The Meaning Layer</em></a> &middot; <a href="https://github.com/nvichare/meaning-layer-starter-kit">GitHub</a>
</p>
