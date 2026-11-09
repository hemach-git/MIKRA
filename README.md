# MIKRA: Manufacturing Intelligent Knowledge Routing Assistant

> **Prototype · SYNTHETIC DATA · local only.** All documents, equipment, people and numbers are fictional.

Floor supervisors ask a plain-English question. A small team of **AI agents** routes it to the right documentation (**Safety procedures, Maintenance manuals or Quality standards**, or more than one), researches each source, and returns a **grounded answer with numbered steps and citations**. Plant managers **approve document updates**, **review flagged answers** and use **query analytics** to spot recurring floor issues.

![Architecture](docs/img/architecture.png)

## Build status (read this first)

| Part | Status |
|---|---|
| Rule-based pipeline, guardrails, document approvals, audit, analytics, feedback queue | **Built and tested** (54 automated tests; 32 rule-based evals on a mock model) |
| **LLM agents:** router, Safety / Maintenance / Quality specialists, synthesizer (OpenAI `gpt-4o-mini`) | **Built**, tested offline with a scripted fake LLM and formally evaluated live on 45 golden cases: **43/45 passed (95.6%)** (see Evaluation results) |
| Streamlit UI | **Built** (`app/main.py` plus Ask, Documents, Review queue, Analytics and Diagnostics pages). Not covered by the automated tests |
| Critic agent, manager insights agent, embedding search, LLM judge | Not built in this prototype. A second AI check on answers is a next step |

**Two kinds of numbers, never mixed:** the 32/32 rule-based result checks the plumbing on a mock model (no AI). The live result (43/45) is the real `gpt-4o-mini` agents on synthetic data.

**Next:** real documents from one plant line, sign-in, faster answers, a second AI check on answers.

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env              # then edit it yourself
streamlit run app/main.py         # http://localhost:8501  (DB auto-seeds on first run)
```

`.env` (never commit it):

```
LLM_PROVIDER=openai               # openai | anthropic | mock
OPENAI_API_KEY=your-key-here
```

`agents.mode` in `config.yaml` selects `multi_agent` or the rule-based `pipeline`. With `LLM_PROVIDER=mock` the app runs fully offline.

| Command | What it does |
|---|---|
| `python -m pytest -q` | Unit, guardrail and service tests (isolated temp DB, no network) |
| `python -m evals.run` | Golden eval → `evals/results/latest.json` |
| `python -m app.data.seed_synthetic --reset` | Rebuild `data/mikra.db` with fresh synthetic data |
| `python scripts/render_mermaid.py` | Diagrams → `docs/img/*.png` (needs Chrome + `pip install playwright`) |
| `python scripts/make_docx.py` / `make_pptx.py` | Regenerate the .docx files and the one-page slide |

## How it works

1. **Guardrails (code):**
   - Checks the question's length and content.
   - Blocks prompt injection and requests to bypass safety controls.
   - Detects emergencies and shows the "call ext. 5555" banner.
   - Masks PII before anything is stored or logged.
2. **Router agent (LLM):** understands the question, picks the sources, extracts the equipment, flags hazards, rewrites one search query per source, and can ask a clarifying question.
3. **Hazard override (code):** keyword rules **or** the router's hazard flag always bring in the Safety specialist. A model mistake cannot drop the safety step.
4. **Specialist agents (LLM + read-only tools):** Safety, Maintenance and Quality each search only their own published manuals (max 3 steps), in parallel, and return cited findings or abstain.
5. **Synthesizer agent (LLM):** merges the findings into one structured answer, safety first.
6. **Grounding check (code):** every citation must be a retrieved section; otherwise it is dropped, and MIKRA **abstains** ("Not found in the approved documentation").
7. **Fallback (code):** an agent error, timeout or token-budget breach falls back to the rule-based pipeline.
8. **Record:** query, citations, agent trace and an audit row, plus a JSON log line (request_id, step timings, tokens, status).

**Where AI is used, and where it deliberately isn't:** the LLM does the language work (understanding, research, writing). Code owns the safety override, published-only filter, step and token caps, grounding check, approvals and audit.

More detail:
- [docs/architecture.md](docs/architecture.md): data flow and sequence diagrams.
- [docs/data_model.md](docs/data_model.md): ERD with PK/FK constraints.
- [docs/design.md](docs/design.md): design, agents and tradeoffs ledger.
- [docs/agents_contract.md](docs/agents_contract.md): agent interfaces.

## Features by user

| Floor Supervisor | Plant Manager |
|---|---|
| Ask with one-click demo questions, even in messy wording | Documents: create draft → **approve/reject** → publish (old version retired, re-indexed) |
| Safety notes first, steps, sources you can open | Review queue for flagged answers (approve/reject, audited) |
| "Not found" instead of guessing | Analytics: KPIs, daily trend, **top recurring issues**, documentation gaps, CSV export |
| Thumbs up / flag a wrong answer | Diagnostics: health, config hash, recent requests, agent trace, eval summary |

## Evaluation results

**v1 rule-based pipeline (mock LLM, synthetic data, 32 golden cases): 32/32 pass.**

| Metric | Result | Target |
|---|---|---|
| Routing accuracy | 100% | ≥ 90% |
| Correct document cited | 100% | ≥ 85% |
| Abstain correctness (out-of-scope) | 100% | 100% |
| Safety-inclusion recall (hazard tasks) | 100% | 100% |
| Draft-document leaks | 0 | 0 |
| p95 latency (pipeline, mock) | ~1 ms | < 8 s agent mode |

Case types: 15 positive, 5 multi-route (maintenance + safety), 5 negative, 7 edge (injection, emergency, draft leak, PII, bad input). Tests: **54/54 pass** (`tests/results/pytest_latest.txt`).

> ⚠️ **With the mock provider, the pass rate checks the pipeline wiring**, not AI quality. The mock is extractive and was written alongside the golden set.

**v2 agents (live `gpt-4o-mini`), formal run: 43/45 passed (95.6%)** on the 45-case golden set. Result file: `evals/results/latest_multi_agent.json` (`python -m evals.run --mode multi_agent`, 2026-11-09).

| Metric | Live result | Target |
|---|---|---|
| Routing accuracy | 100% | ≥ 90% |
| Correct document cited | 97.1% | ≥ 85% |
| Abstain correctness (out-of-scope) | 100% | 100% |
| Safety-inclusion recall (hazard tasks) | 100% | 100% |
| Paraphrased questions | 100% | ≥ 80% |
| Draft-document leaks | 0 | 0 |
| Latency p50 / p95 | 5.8 s / 9.8 s | p95 < 8 s: **not met** |
| LLM calls and tokens per question | ~3.0 calls, ~2,000 tokens | |
| Estimated cost | ~$0.02 for the whole run (~$0.0005 per question; estimate from the price table in `evals/run.py`) | |
| Fell back to rule-based mode | 0 cases | |

By case type: hazard 66.7% (2 of 3), positive 93.3% (14 of 15), every other type 100%.

**The 2 failures, and 1 warning**
- **P11** "What dry film thickness is acceptable for paint?": the answer was missing the 60-80 micron value (incomplete answer).
- **H02** "need to swap a seized roller under the C3 belt": the maintenance manual was not cited; only the emergency SOP was (missing citation).
- 1 answer carried an irrelevant safety note (flagged as a warning, not a failure).

The checks are routing, citation and keyword rules, not an AI judge, and the set is synthetic and small (45 cases).

## Governance

| Item | Where it lives |
|---|---|
| Config of record | `config.yaml`; its hash is stored on every `ask` audit row and in every eval result |
| Data-sources and model register | [docs/data_sources.md](docs/data_sources.md); every seeded row has `is_synthetic=1` |
| Audit trail | `audit_log` table: who, role, action, target, decision, model, request_id, details |
| Human-in-the-loop | Document publishing **requires** manager approval; flagged answers need a manager decision; **agents have read-only tools and cannot write or publish** |
| Logs | JSON lines in `logs/app.jsonl`, PII-masked |
| Data leaving the machine | In agent mode the PII-masked question and retrieved sections go to the LLM API. Fine for synthetic data; real documents need a review first |

## Assumptions and limitations

- The role selector is **not** authentication (a later version adds SSO).
- Live quality was measured on 45 **synthetic** cases (43/45); it is not a guarantee for real documents. A small model can vary between runs, and the checks are citation and keyword based (no AI judge), so a wrong sentence that cites a real section could still pass.
- Live latency misses the 8 s goal: p50 5.8 s, p95 9.8 s.
- Agent mode makes several LLM calls per question, so latency is higher than the rule-based pipeline.
- BM25 keyword search plus agent query rewriting suits ~100 sections; larger corpora need hybrid search.
- SQLite, single node, local only. Markdown documents only (no PDF/OCR yet).

## Deliverables

| Deliverable | Files |
|---|---|
| Scope | `docs/scope.md` / `.docx` |
| Estimates and risks | `docs/estimates_risks.md` / `.docx` |
| Design | `docs/design.md` / `.docx` |
| One-page slide (plain English, for plant managers and business leaders) | `docs/one_pager_deck.pptx` |
| Session briefs | `docs/frontend_brief.md`, `docs/tests_evals_brief.md` |
