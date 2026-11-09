# MIKRA: Data Model

SQLite with `PRAGMA foreign_keys=ON` on every connection. CHECK constraints enforce allowed values. Every seeded row has `is_synthetic=1`.

```mermaid
%% name: data_model
erDiagram
  DOCUMENTS ||--o{ CHUNKS : "split into"
  QUERIES ||--o{ CITATIONS : "cites"
  CHUNKS ||--o{ CITATIONS : "cited by"
  QUERIES ||--o{ FEEDBACK : "rated by"
  DOCUMENTS {
    text doc_id PK
    text doc_key
    int version
    text category
    text status
    text owner
    text reviewed_by
    int is_synthetic
  }
  CHUNKS {
    text chunk_id PK
    text doc_id FK
    int section_no
    text section
    text text
  }
  QUERIES {
    text query_id PK
    text request_id
    text role
    text question_masked
    text routed_categories
    text primary_category
    real route_confidence
    text status
    text equipment_tag
    real latency_ms
    text model
    int is_synthetic
  }
  CITATIONS {
    text query_id FK
    text chunk_id FK
    int rank
    real score
  }
  FEEDBACK {
    int feedback_id PK
    text query_id FK
    int rating
    text review_status
    text reviewed_by
  }
  AUDIT_LOG {
    int audit_id PK
    text ts
    text actor
    text action
    text target
    text decision
    text model
    text request_id
  }
```

| Table | Purpose | Key rules |
|---|---|---|
| documents | One row per document **version** | `UNIQUE(doc_key, version)`; status ∈ draft/published/rejected/retired; only one pending draft per doc_key; category can't change between versions |
| chunks | Section-level text (split on `## ` headings) | FK → documents; chunk_id = `<doc_id>#s<n>` so citations always point at an exact version and section |
| queries | Every question asked, including blocked and abstained ones | PII masked before storage; status ∈ ok/abstained/blocked/error |
| citations | Which sections supported each answer | Composite PK; FKs to queries and chunks |
| feedback | Thumbs up/down; thumbs-down goes to the manager review queue | review_status ∈ n/a/pending/approved/rejected; can't be resolved twice |
| audit_log | Who did what, when, with which model and request_id | Written in the same transaction as the action |
