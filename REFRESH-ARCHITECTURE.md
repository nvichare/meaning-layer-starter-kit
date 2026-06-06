# Continuous Ontology Refresh Architecture

> Use deterministic systems to detect objective changes. Use AI to interpret the meaning, rank the business impact, draft ontology changes, and route the proposal to the correct steward. Do not allow an LLM to silently rewrite the enterprise ontology.

This document describes how to evolve the starter kit from a scheduled review checker into an ontology observability and continuous-refresh service.

## Architecture

```
                ┌─────────────────────────────────────┐
                │         Enterprise Systems          │
                │                                     │
                │ Warehouses  dbt  BI  Catalog  DQ    │
                │ Lineage  Agents  Search  Tickets    │
                └─────────────────┬───────────────────┘
                                  │
                                  ▼
                ┌─────────────────────────────────────┐
                │        Signal Collection Layer      │
                │                                     │
                │ Schema snapshots                    │
                │ dbt artifacts                       │
                │ OpenLineage events                  │
                │ Quality incidents                   │
                │ Search telemetry                    │
                │ Agent traces and feedback           │
                └─────────────────┬───────────────────┘
                                  │
                                  ▼
                ┌─────────────────────────────────────┐
                │       Deterministic Detection       │
                │                                     │
                │ Diffing  Rules  Thresholds  Alerts  │
                └─────────────────┬───────────────────┘
                                  │
                                  ▼
                ┌─────────────────────────────────────┐
                │          AI Interpretation          │
                │                                     │
                │ Classify  Cluster  Summarize        │
                │ Map concepts  Assess impact         │
                │ Draft definitions  Recommend action │
                └─────────────────┬───────────────────┘
                                  │
                                  ▼
                ┌─────────────────────────────────────┐
                │        Governed Proposal Queue      │
                │                                     │
                │ Evidence  Confidence  Steward       │
                │ Diff  Impacted assets  Approval     │
                └─────────────────┬───────────────────┘
                                  │
                                  ▼
                ┌─────────────────────────────────────┐
                │    Validate, Approve and Publish    │
                │                                     │
                │ SHACL  Git PR  Steward review       │
                │ Catalog sync  Context API refresh   │
                └─────────────────────────────────────┘
```

## The eleven signal types

| # | Signal | Detection | AI adds value by |
|---|--------|-----------|-----------------|
| 1 | Schema drift | Deterministic diff of snapshots | Interpreting whether new fields are new concepts, synonyms, or policy triggers |
| 2 | Lineage changes | Graph edge diff over time | Assessing whether upstream changes alter metric meaning |
| 3 | Quality incidents | Threshold alerts from DQ tools | Mapping affected columns to concepts, ranking downstream impact |
| 4 | New dbt models | Manifest diff | Mapping to existing concepts or proposing new ones |
| 5 | New semantic-layer metrics | Semantic manifest diff | Detecting duplicates, variants, or conflicts with existing metrics |
| 6 | Catalog no-result searches | Aggregate frequency by domain | Clustering into missing synonyms or undocumented concepts |
| 7 | Agent low-confidence responses | Instrument retrieval scores | Identifying missing ontology coverage |
| 8 | Repeated user clarifications | Capture correction turns | Detecting missing concept variants and domain-specific definitions |
| 9 | Dashboard definition disagreements | Extract and normalize formulas | Reconciling conflicting implementations |
| 10 | Heavily used but weakly governed | Usage score vs governance score | Prioritizing remediation by business impact |
| 11 | Unused concepts | Zero-usage thresholds | Distinguishing truly obsolete from seasonal or regulatory |

## The design rule

| Category | Automation level |
|----------|-----------------|
| Objective observation | Fully automated |
| Interpretation and recommendation | AI-assisted |
| Enterprise meaning change | Human-approved and version-controlled |

## Implementation phases

**Phase 1 (foundation):** Review overdue, dbt models, semantic metrics, lineage changes, quality incidents

**Phase 2 (usage learning):** Catalog searches, agent failures, user clarifications, weak governance

**Phase 3 (rationalization):** Dashboard disagreements, unused concept deprecation

See the full specification with code examples, AI techniques, guardrails, and demo scenarios in the book's companion documentation.
