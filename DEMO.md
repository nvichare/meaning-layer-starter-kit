# The Meaning Layer Starter Kit: Demo Guide

Use the starter kit as a **small, controlled proof of value**. It is designed to demonstrate that enterprise meaning can be modeled, governed, validated, refreshed, synchronized into a catalog, and consumed by an AI application without requiring a large knowledge-graph program upfront.

## 1. What the demonstration should prove

| Question | What the starter kit demonstrates |
|----------|-----------------------------------|
| Can we define enterprise meaning formally without making it too complex? | A small RDF/SKOS ontology with understandable Turtle files |
| Can we stop poor-quality definitions from entering the meaning layer? | SHACL validation blocks incomplete metrics, invalid statuses, missing owners, and missing asset links |
| Can AI applications retrieve approved definitions rather than improvise? | A context API returns the governed definition, calculation logic, steward, and mapped data asset |
| Can the ontology remain current? | A refresh script detects overdue reviews and generates proposals |
| Can the meaning layer feed existing catalog tools? | The kit exports glossary terms and produces Atlan and OpenMetadata payloads |
| Can this become an operating process rather than a one-time exercise? | GitHub CI validates every proposed ontology change before publication |

> AI can help discover and propose meaning, but approved enterprise meaning must be versioned, governed, validated, and reusable across catalogs, analytics, and AI applications.

---

## 2. The business story

The ontology contains:

| Concept | Meaning | Steward | Linked asset |
|---------|---------|---------|--------------|
| Customer | A party with an active or historical commercial relationship with the enterprise | Customer Data Council | Customer master table |
| Active Customer | A customer with at least one qualifying transaction in the trailing 12 months | Growth Analytics | Customer 360 view |
| Net Revenue | Recognized gross revenue less discounts, returns, credits, and rebates | Finance Analytics | Revenue mart |
| Customer PII Policy | Customer-identifying fields must be masked outside approved workflows | Privacy Office | Policy concept |

The demo story:

1. Finance wants AI agents, dashboards, and business teams to use the same definition of **Net Revenue**.
2. A team proposes a new metric called **Churn Risk**.
3. The proposed metric is incomplete.
4. The governance pipeline rejects it automatically.
5. The approved definitions are exported to the enterprise catalog.
6. An AI agent retrieves the approved meaning through an API.
7. The refresh process detects that **Active Customer** has not been reviewed recently and generates a steward action.

This shows the full flywheel in less than 30 minutes.

---

## 3. Setup

```bash
unzip enterprise_ontology_practitioner_kit.zip
cd enterprise_ontology_practitioner_kit

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

No external catalog tenant, database, or cloud account is required for the first demonstration.

---

## 4. Demo sequence: the 25-minute walkthrough

### Step 1: Show the ontology model

Open `ontology/enterprise_ai.ttl`. Show the `NetRevenueTerm` concept:

```turtle
ex:NetRevenueTerm a skos:Concept, ex:MetricConcept ;
  skos:inScheme ex:EnterpriseBusinessVocabulary ;
  skos:prefLabel "Net Revenue"@en ;
  skos:definition "Recognized gross revenue less contractual discounts, returns, credits, and rebates."@en ;
  ex:calculationLogic "SUM(gross_revenue - discounts - returns - credits - rebates)" ;
  ex:steward "Finance Analytics" ;
  ex:status "Approved" ;
  ex:lastReviewedAt "2026-04-15"^^xsd:date ;
  ex:reviewCadenceDays 60 ;
  ex:implementedByAsset ex:RevenueMart ;
  ex:dependsOnConcept ex:CustomerTerm .
```

The ontology connects the definition to a stable URI, a concept type, a deterministic calculation, a steward, a lifecycle status, a review cadence, a dependent concept, and an implementing data asset. That is the difference between a static glossary and an operational meaning layer.

### Step 2: Show the governance rules

Open `ontology/shapes.ttl`. These are SHACL controls that behave like automated policy checks:

```turtle
ex:MetricConceptShape a sh:NodeShape ;
  sh:targetClass ex:MetricConcept ;
  sh:property [
    sh:path ex:calculationLogic ;
    sh:minCount 1 ;
    sh:message "A governed metric requires deterministic calculation logic." ;
  ] ;
  sh:property [
    sh:path ex:implementedByAsset ;
    sh:minCount 1 ;
    sh:message "A governed metric must link to at least one implementing data asset." ;
  ] .
```

AI-generated definitions can sound plausible while remaining operationally useless. SHACL forces the proposal to meet enterprise controls.

### Step 3: Validate the approved graph

```bash
make validate
```

Expected:

```
SHACL conforms: True
Triples validated: 167
All ontology governance controls passed.
```

### Step 4: Demonstrate how the governance gate rejects weak definitions

```bash
make validate-invalid
```

Expected (6 violations):

```
SHACL conforms: False
Triples validated: 177

Lifecycle status must be Draft, Approved, or Deprecated.
A governed metric must link to at least one implementing data asset.
A governed metric requires deterministic calculation logic.
Each data asset requires an accountable owner or steward.
Each data asset requires an asset type.
Every governed concept requires a positive review cadence.
```

> This is where governance becomes executable. A pull request cannot publish an incomplete metric merely because the wording sounds credible.

### Step 5: Show how an AI agent retrieves governed meaning

```bash
make query
```

Expected:

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

Start the context API:

```bash
make api
```

Query it:

```bash
curl "http://127.0.0.1:8000/concepts/Net%20Revenue"
```

Query a non-existent concept:

```bash
curl -i "http://127.0.0.1:8000/concepts/Invented%20Metric"
# Returns: 404 Not Found - {"detail":"Concept not found"}
```

The AI agent should react to the 404 by asking for clarification or escalating to a steward. It should not manufacture a definition. That is a critical control for enterprise AI.

### Step 6: Demonstrate the refresh flywheel

```bash
make refresh
```

Expected:

```
Generated 1 refresh proposal(s) as of 2026-06-05.
1. [REVIEW_OVERDUE] Active Customer: Assign steward review task and run lineage impact analysis before republishing.
```

The refresh process can later detect: schema drift, lineage changes, quality incidents, new dbt models, catalog searches with no result, agent low-confidence responses, concepts heavily used but weakly governed, concepts no longer used.

### Step 7: Demonstrate catalog propagation

```bash
make export
```

Expected:

```
Exported 4 catalog-ready glossary terms to catalog_sync/glossary_terms.csv
```

---

## 5. Catalog integration

### Atlan

```bash
make sync-atlan
```

Generates `catalog_sync/atlan_business_graph_import.csv`. For production, replace with `pyatlan` SDK integration.

### OpenMetadata

```bash
make sync-openmetadata
```

Dry-run mode. To connect a real environment:

```bash
export OPENMETADATA_BASE_URL="https://your-openmetadata-host/api"
export OPENMETADATA_TOKEN="your-token"
python src/sync_openmetadata.py --apply
```

### Alation

Use `catalog_sync/glossary_terms.csv` as the canonical source and map columns into an Alation glossary import.

### Vendor evaluation criteria

| Capability | Required behavior |
|------------|-------------------|
| Stable concept URI | Must remain attached to the catalog term |
| Definition | Must preserve the approved business definition |
| Synonyms | Must improve discoverability |
| Parent relationship | Must support concept hierarchy |
| Steward | Must identify accountable ownership |
| Lifecycle | Must support draft, approved, and deprecated states |
| Review date | Must support recertification workflows |
| Asset links | Must connect definitions to physical or semantic assets |
| Workflow | Must support proposal, review, approval, and propagation |
| API or automation | Must allow synchronization without manual re-entry |

---

## 6. CI/CD operating model

The repository includes `.github/workflows/ontology-ci.yml`. Every pull request runs validation, query, refresh, and export.

### Live GitHub demonstration

```bash
git checkout -b demo/churn-risk-term
# Copy invalid data, commit, open PR -- CI fails
# Fix the concept, push -- CI passes
```

This demonstrates: Proposal -> Automated validation -> Steward review -> Merge -> Catalog sync -> Runtime publication.

---

## 7. Three demos for different audiences

### Executive demo (12 minutes)

| Time | Demonstration |
|------|---------------|
| 2 min | Explain the problem: AI, analytics, and business teams use inconsistent meanings |
| 2 min | Show the ontology graph and the Net Revenue definition |
| 3 min | Run `make validate-invalid` -- weak definitions are rejected |
| 2 min | Run the context API lookup for Net Revenue |
| 2 min | Run `make refresh` -- stale concept detected |
| 1 min | Show the catalog propagation output |

### Architecture demo (30 minutes)

RDF/SKOS modeling, OWL classes, SHACL validation, Git lifecycle, context API, refresh proposals, catalog export, Atlan/OpenMetadata adapters, GitHub CI, runtime options (Stardog, GraphDB, Jena).

### Vendor proof-of-value workshop (60-90 minutes)

Give each catalog vendor `catalog_sync/glossary_terms.csv` and score against `docs/vendor_options_scorecard.csv`.

---

## 8. Convert to a real enterprise proof of value

Replace starter-kit concepts with 5-10 real concepts from one domain:

| Domain | Starter concepts |
|--------|-----------------|
| Finance | Net Revenue, Gross Margin, Bookings, ARR, Recognized Revenue |
| Customer analytics | Customer, Active Customer, Churn, Customer Segment, Lifetime Value |
| AI operations | Incident, Service, Application, Change Request, Root Cause, MTTR |
| Supply chain | Part, Inventory Position, Safety Stock, Supplier, Purchase Order, Lead Time |

For each concept, require: stable URI, preferred name, synonyms, business definition, steward, lifecycle status, review cadence, calculation logic (if metric), mapped catalog asset, dependent concepts, policy links, AI use cases.

---

## 9. Measure whether the proof of value worked

| Metric | What to measure |
|--------|-----------------|
| AI grounding quality | Reduction in unsupported or inconsistent AI answers |
| Metric consistency | Reduction in conflicting dashboard calculations |
| Search effectiveness | Improvement in catalog search success and synonym discovery |
| Steward accountability | Percentage of critical concepts with owners and review dates |
| Change responsiveness | Time between schema drift and approved ontology update |
| Reuse | Number of AI applications, dashboards, and assets consuming the same concept |
| Governance automation | Percentage of weak proposals rejected automatically |
| Adoption | Number of active users retrieving or contributing governed definitions |

The full lifecycle:

```
Business definition -> Formal ontology -> Validation controls -> Steward approval
-> Catalog synchronization -> AI and analytics consumption -> Usage and drift signals
-> Refresh proposal -> (repeat)
```

The most persuasive demonstration is the contrast between the valid Net Revenue concept and the rejected Churn Risk proposal. It makes the value visible immediately.
