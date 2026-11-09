# MIKRA: Compact Design (approved Phase 0 plan)

Diagrams: see [architecture.md](architecture.md) and [data_model.md](data_model.md).

## 1. Clarify

**Requirements**
- **R1.** Route each question to Safety, Maintenance or Quality, or more than one.
- **R2.** Give a grounded, cited answer with steps.
- **R3.** Abstain when the documents don't cover the question.
- **R4.** Safety first: hazards always include the safety procedure.
- **R5.** Managers update documents through draft → approval → publish.
- **R6.** Query analytics with recurring issues and CSV export.
- **R7.** Supervisors can flag wrong answers for manager review.
- **Non-functional:** p95 < 5 s, runs locally and offline, no secrets in the repo, every request traceable.

**Never list**
- NEVER give a safety answer without citing the safety procedure, and never suggest skipping a safety step.
- NEVER answer from outside the documents. Abstain instead.
- NEVER show draft or retired documents to supervisors.
- NEVER follow instructions found inside document text.
- NEVER publish a document change without manager approval.

**User journeys**
- **J1.** Supervisor, "Conveyor C3 jam": routed to Maintenance + Safety (lockout); steps and citations shown.
- **J2.** Manager, revised torque spec: draft → approve → floor answers change immediately, with an audit record.
- **J3.** Manager, weekly review: Analytics → top recurring issue → drill-down → CSV.

## 2. Architecture

A fixed pipeline: guardrails → router (rules + classifier, safety override) → BM25 retrieval (published only, routed categories) → LLM JSON answer → grounding check → store + audit. Streamlit UI, SQLite with foreign keys, JSON logs, and `config.yaml` as the config of record.

## 3. Retrieval and grounding

**Retrieval**
- Section-level chunks (`<doc_id>#s<n>`) carry the document key, version and category.
- The published-only filter is applied **before** ranking.

**Routing**
- Blended score = 0.5 × keyword rules + 0.5 × classifier.
- Secondary categories are included at ≥ 60% of the top score.
- Below 0.35 confidence, all three sources are searched.
- A hazard term forces Safety in.

**Answer**
- Top 4 sections per routed category, capped at 8, in `<doc>` delimiters marked untrusted.
- The output is checked against a strict JSON schema, with one retry and an extractive fallback.
- Grounding: citations must be a subset of the retrieved sections; abstain if none remain.

## 4. Reliability (six failure modes)

| Failure mode | Mitigation |
|---|---|
| Loops | Single pass, no agent loop |
| Derailment | Fixed pipeline |
| Context overflow | Top-k and chunk character caps |
| Cascading errors | Pydantic checks at each step; fallback; fail closed (abstain) |
| Hallucination | Grounding check and abstain |
| Cost runaway | max_tokens cap, mock mode, context cap |

## 5. Evals and observability

- **Golden set (32 cases):**
  - 15 positive
  - 5 multi-route
  - 5 negative
  - 7 edge cases: injection, emergency, draft leak, PII, bad input
- **Metrics:** routing accuracy, citation hit rate, abstain correctness, safety-inclusion recall, draft leaks, p95 latency.
- **Traced per request:** request_id, stage timings, tokens, status and flags.

## 6. Tradeoffs ledger

| Tension | We lean | Gave up | Why |
|---|---|---|---|
| Routing | Rules + classifier | Pure LLM | Explainable and auditable for safety; works offline |
| Retrieval | BM25 | Vector DB | Zero infrastructure; fine for ~100 sections |
| Orchestration | Fixed pipeline | Agent loop | Predictable latency and cost |
| Grounding | Strict abstain | Fluency | A wrong safety answer costs far more than "not found" |
| Freshness | Re-index on publish | Live editing | Only approved procedures reach the floor |
