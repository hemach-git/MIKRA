# MIKRA: Data Model

SQLite with `PRAGMA foreign_keys=ON` on every connection. CHECK constraints enforce allowed values. Every seeded row has `is_synthetic=1`.

> **Status:** the tables below are implemented except `AGENT_STEPS`, which is **planned for v2**. Until it lands, the agent trace is returned in `AskResponse.agent_trace` and written to the JSON logs.

```mermaid
%% name: data_model
erDiagram
  DOCUMENTS ||--o{ CHUNKS : "split into"
  QUERIES ||--o{ CITATIONS : "cites"
  CHUNKS ||--o{ CITATIONS : "cited by"
  QUERIES ||--o{ FEEDBACK : "rated by"
  QUERIES ||--o{ AGENT_STEPS : "traced by"
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
  AGENT_STEPS {
    int step_id PK
    text query_id FK
    int seq
    text agent
    text kind
    text model
    int tokens_in
    int tokens_out
    real latency_ms
    text status
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
| chunks | Section-level text (split on `## ` headings) | FK → documents; chunk_id = `<doc_id>#s<n>` so citations point at an exact version and section |
| queries | Every question asked, including blocked and abstained ones | PII masked before storage; status ∈ ok/abstained/blocked/error |
| citations | Which sections supported each answer | Composite PK; FKs to queries and chunks |
| feedback | Thumbs up/down; thumbs-down goes to the manager review queue | review_status ∈ n/a/pending/approved/rejected; can't be resolved twice |
| agent_steps *(planned)* | One row per agent step: LLM call, tool call or guard | FK → queries; tokens, latency and status per step, so cost and slow agents are visible |
| audit_log | Who did what, when, with which model and request_id | Written in the same transaction as the action. v2 adds the prompt version and `agents.mode` in `details` |
