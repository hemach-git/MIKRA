# MIKRA: Manufacturing Intelligent Knowledge Routing Assistant

> **Prototype · SYNTHETIC DATA · local only.** All documents, equipment, people and numbers are fictional.

Floor supervisors ask a plain-English question. MIKRA **routes** it to the right documentation (**Safety procedures, Maintenance manuals or Quality standards**, or more than one) and returns a **grounded answer with numbered steps and citations**. Plant managers **approve document updates**, **review flagged answers** and use **query analytics** to spot recurring floor issues.

![Architecture](docs/img/architecture.png)

## Quick start (Windows / macOS / Linux)

```bash
pip install -r requirements.txt
cp .env.example .env              # optional; defaults to LLM_PROVIDER=mock
streamlit run app/main.py         # http://localhost:8501  (DB auto-seeds on first run)
```

| Command | What it does |
|---|---|
| `python -m pytest -q` | 29 unit, guardrail and service tests (isolated temp DB) |
| `python -m evals.run` | 32-case golden eval → `evals/results/latest.json` |
| `python -m app.data.seed_synthetic --reset` | Rebuild `data/mikra.db` with fresh synthetic data |
| `python scripts/render_mermaid.py` | Diagrams → `docs/img/*.png` (needs Chrome + `pip install playwright`) |
| `python scripts/make_docx.py` / `make_pptx.py` | Regenerate the .docx files and the one-page slide |

**Using a live LLM (later):** set `LLM_PROVIDER=anthropic` and `ANTHROPIC_API_KEY` in `.env`, run `pip install anthropic`, then re-run `python -m evals.run`. Never commit keys.

## How it works

1. **Guardrails:**
   - Checks the question's length and content.
   - **Blocks prompt injection and requests to bypass safety controls.**
   - Detects emergencies and shows the "call ext. 5555" banner.
   - Masks PII before anything is stored or logged.
2. **Router:**
   - Blends keyword rules with a classifier (mock now, LLM later).
   - Below 0.35 confidence, it searches all sources.
   - **Hazard terms (jam, die change, leak…) always add the Safety source.**
3. **Retriever:** BM25 over section-level chunks, **published documents only**, scoped to the routed categories.
4. **Answer:**
   - Strict JSON output (answer, steps, citation_ids, safety_notes, confidence, abstain), with one retry and an extractive fallback.
   - **Grounding check:** citations must be retrieved sections. Otherwise MIKRA **abstains** ("Not found in the approved documentation").
5. **Record:** query, citations and an audit row, plus a JSON log line (request_id, stage timings, tokens, status).

More detail:
- [docs/architecture.md](docs/architecture.md): data flow and sequence diagrams.
- [docs/data_model.md](docs/data_model.md): ERD with PK/FK constraints.
- [docs/design.md](docs/design.md): design and tradeoffs ledger.

## Features by user

| Floor Supervisor | Plant Manager |
|---|---|
| Ask with one-click demo questions | Documents: create draft → **approve/reject** → publish (old version retired, re-indexed) |
| Safety notes first, steps, sources you can open | Review queue for flagged answers (approve/reject, audited) |
| "Not found" instead of guessing | Analytics: KPIs, daily trend, **top recurring issues**, documentation gaps, CSV export |
| Thumbs up / flag a wrong answer | Diagnostics: health, config hash, recent requests, eval summary |

## Evaluation results (latest run)

Mock LLM, synthetic data, 32 golden cases: **32/32 pass**.

| Metric | Result | Target |
|---|---|---|
| Routing accuracy | 100% | ≥ 90% |
| Correct document cited | 100% | ≥ 85% |
| Abstain correctness (out-of-scope) | 100% | 100% |
| Safety-inclusion recall (hazard tasks) | 100% | 100% |
| Draft-document leaks | 0 | 0 |
| p95 latency (pipeline, mock) | ~1 ms | < 5 s |

Case types:
- 15 positive
- 5 multi-route (maintenance + safety)
- 5 negative (off-topic or not in the documents)
- 7 edge: injection, emergency, draft leak, PII, bad input

Tests: **29/29 pass** (`tests/results/pytest_latest.txt`).

> ⚠️ **With the mock provider, the pass rate checks the pipeline wiring** (routing, retrieval, guardrails, grounding), **not live LLM answer quality**. The mock is extractive and was written alongside the golden set. **Live LLM evaluation is deferred** until an API key is configured.

## Governance

| Item | Where it lives |
|---|---|
| Config of record | `config.yaml`; its hash is stored on every `ask` audit row and in every eval result |
| Data-sources register | [docs/data_sources.md](docs/data_sources.md); every seeded row has `is_synthetic=1`, and analytics separates "synthetic" from "live demo" |
| Audit trail | `audit_log` table: who, role, action, target, decision, model, request_id, details |
| Human-in-the-loop | Document publishing **requires** manager approval; flagged answers need a manager decision |
| Logs | JSON lines in `logs/app.jsonl`, PII-masked |

## Assumptions and limitations

- The role selector is **not** authentication (v1 adds SSO).
- The mock LLM gives extractive answers: accurate quotes, but not conversational. The `anthropic` provider is wired but **not validated yet**.
- BM25 keyword search can miss synonyms ("stuck" vs "jam"). v1 adds hybrid vector search.
- SQLite, single node, local only. Markdown documents only (no PDF/OCR yet).

## Deliverables

| Deliverable | Files |
|---|---|
| Scope | `docs/scope.md` / `.docx` |
| Estimates and risks | `docs/estimates_risks.md` / `.docx` |
| Design | `docs/design.md` / `.docx` |
| One-page slide | `docs/one_pager.pptx` |
| Frontend brief | `docs/frontend_brief.md` |
