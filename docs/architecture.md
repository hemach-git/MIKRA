# MIKRA: Architecture

MIKRA (Manufacturing Intelligent Knowledge Routing Assistant) routes floor supervisors' questions to the right approved documentation and returns grounded, cited answers. All data is **synthetic**.

## 1. Solution architecture

```mermaid
%% name: architecture
flowchart LR
  S[Floor Supervisor] --> ASK[Ask page]
  M[Plant Manager] --> ADM[Docs, Review, Analytics, Diagnostics]
  ASK --> WF[Workflow]
  WF --> G[Guardrails]
  WF --> R[Router]
  R --> RET[BM25 Retriever]
  WF --> RET
  WF --> L[LLM: mock or Claude]
  WF --> AU[Audit]
  ADM --> DA[Docs Admin]
  ADM --> AN[Analytics]
  ADM --> AU
  DA --> RET
  RET --> DB[(SQLite)]
  DA --> DB
  AN --> DB
  AU --> DB
  WF --> LOG[JSON Logs]
  CFG[config.yaml] -.-> WF
```

| Component | Responsibility | Business "why" |
|---|---|---|
| Workflow | Fixed pipeline: guardrails → route → retrieve → answer → grounding check → store | Predictable latency and cost; no runaway agent loop on the floor |
| Guardrails | Length/type checks, prompt-injection and safety-bypass blocking, emergency detection, PII masking | Protects people and keeps logs compliant |
| Router | Keyword rules + classifier (LLM or mock), blended; hazard terms force the Safety source in | Explainable, auditable routing; safety is never missed |
| Retriever | BM25 over section-level chunks, **published documents only**, scoped to routed categories | Zero infrastructure; supervisors only see approved procedures |
| LLM Client | `mock` (deterministic, extractive) or `anthropic`; strict JSON output, retry, fallback | Demo works offline; swap to a live model with one setting |
| Docs Admin | Draft → manager approval → published (old version retired) → re-index | Only approved procedures reach the floor |
| Audit | Every ask, feedback, review and publish recorded with actor, decision, model, request_id | Traceability for EHS/quality audits |
| Analytics | KPIs, trends, recurring issues and documentation gaps computed from records | Managers spot recurring floor issues |

## 2. Data flow

```mermaid
%% name: data_flow
flowchart TD
  Q[Supervisor question] --> V{Guardrails}
  V -- injection or bad input --> B[Blocked + logged]
  V -- ok --> E{Emergency?}
  E -- yes --> EB[Red banner + emergency SOP]
  E -- no --> RT[Route: rules + classifier]
  EB --> RT
  RT --> H{Hazard?}
  H -- yes --> SF[Add Safety source]
  H -- no --> RE[Retrieve published sections]
  SF --> RE
  RE --> T{Evidence strong enough?}
  T -- no --> AB[Abstain: not in docs]
  T -- yes --> GEN[Generate JSON answer]
  GEN --> GC{Citations grounded?}
  GC -- no --> AB
  GC -- yes --> OUT[Answer + steps + safety notes + citations]
  OUT --> ST[(Store query, citations, audit)]
  AB --> ST
  B --> ST
  ST --> FB[Feedback: flag wrong answer]
  FB --> HR[Manager review queue]
  ST --> KPI[Analytics dashboard]
```

## 3. Request sequence (one question, end to end)

```mermaid
%% name: sequence
sequenceDiagram
  actor S as Supervisor
  participant UI as Streamlit
  participant WF as Workflow
  participant G as Guardrails
  participant R as Router
  participant RET as Retriever
  participant L as LLM
  participant DB as SQLite
  S->>UI: How do I clear a jam on Conveyor C3?
  UI->>WF: ask(question, role, user)
  WF->>G: validate, mask PII, emergency check
  G-->>WF: ok
  WF->>R: route(question)
  R-->>WF: maintenance + safety (hazard: jam)
  WF->>RET: search(published, routed categories)
  RET-->>WF: MM-CONV-02 s2, SOP-LOTO-04 s1
  WF->>L: delimited docs + question
  L-->>WF: JSON answer with citation ids
  WF->>WF: schema check + grounding check
  WF->>DB: query, citations, audit row
  WF-->>UI: AskResponse
  UI-->>S: Safety note, steps, sources
```

## 4. File structure

```
mfg-doc-router/
├── app/
│   ├── main.py, pages/, ui/          Streamlit frontend (parallel session)
│   ├── services/                     interface contract used by the UI
│   │   ├── workflow.py               orchestration: ask(), health()
│   │   ├── router.py                 rules + classifier + safety override
│   │   ├── retriever.py              BM25 per category, published-only
│   │   ├── llm.py                    mock / anthropic, prompts, JSON output
│   │   ├── guardrails.py             validation, injection, emergency, PII
│   │   ├── docs_admin.py             draft → approve → publish lifecycle
│   │   ├── audit.py                  audit trail, feedback, review queue
│   │   └── analytics.py              KPIs, trends, gaps, CSV
│   ├── models/schemas.py             Pydantic contract
│   ├── data/db.py, seed_synthetic.py, corpus/*.md (18 synthetic docs + 1 draft)
│   └── observability/logging.py      JSON logs with request_id
├── evals/ golden.jsonl, run.py, results/
├── tests/                            pytest (29 tests)
├── docs/                             design, architecture, data model, scope, risks, slide
├── scripts/                          render_mermaid.py, make_docx.py, make_pptx.py
└── config.yaml, .env.example, requirements.txt, README.md
```
