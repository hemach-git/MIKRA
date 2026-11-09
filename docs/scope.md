# MIKRA: Scope Document (v2: AI-powered, supervised multi-agent)

**Project:** MIKRA (Manufacturing Intelligent Knowledge Routing Assistant)
**Client problem:** A plant operator wants floor supervisors to get answers from the right documentation (safety procedures, maintenance manuals or quality control standards), routed automatically and answered accurately.
**Engagement:** 2.5-hour prototype, local deployment only, **synthetic data**.

> **Status (2026-11-09).** The rule-based version (v1) and the Streamlit UI are built; v1 is tested (29/29 tests, 32/32 evals on a mock model, which checks wiring only). The AI agent layer (v2) is **built** and was checked live in an informal 9-question live quick check, not a full evaluation. The formal live evaluation is run by a separate session; its results were not available when this document was updated, so section 6 reports quick-check figures only, labelled as such.

## 1. Business problem

Floor supervisors resolve issues during live production: jams, alarms, out-of-spec parts, PPE questions. Today they look through three separate binders. That causes:
- **Downtime:** minutes lost per issue searching for the right procedure.
- **Safety risk:** a maintenance fix done without the matching lockout procedure.
- **Quality escapes:** using an outdated spec, or a draft spec that was never approved.
- **No visibility:** managers can't see which issues keep recurring on the floor.

## 2. Users

| User | Needs | What MIKRA gives them |
|---|---|---|
| Floor Supervisor (primary) | Fast, reliable answers during operations, even when the question is loosely worded | One question box; an AI agent team routes it, researches the right manuals and returns a cited answer with steps; safety first; "not found" instead of a guess |
| Plant Operator / Manager (admin) | Keep documentation current; see recurring issues | Draft → approve → publish workflow; review queue for flagged answers; analytics of recurring issues and documentation gaps |

## 3. How AI is used (v2)

| Capability | AI or code | Status |
|---|---|---|
| Understand intent, pick sources, extract equipment, rewrite search queries | **Router agent (LLM)** | Built; live quick check only |
| Research each source with search tools, return cited findings | **Safety / Maintenance / Quality agents (LLM + tools)** | Built; live quick check only |
| Merge findings into one structured, cited answer | **Synthesizer agent (LLM)** | Built; live quick check only |
| Safety override, published-only filter, grounding check, step and token caps, approvals, audit | **Code (deliberately not AI)** | Built |
| Rule-based router and extractive answer (fallback) | Code | Built, tested |
| Critic agent, insights agent, semantic search, LLM judge | LLM | Not built (a second AI check on answers is next) |

## 4. In scope

**Built and tested (v1)**
1. Question routing to Safety, Maintenance or Quality (rules + classifier), with a hazard → Safety override.
2. Grounded answers with steps, safety notes, citations and confidence; abstain when the documents don't cover the question.
3. Guardrails: injection and bypass blocking, emergency banner, PII masking, untrusted document text.
4. Document lifecycle: draft → manager approval → published (previous version retired). Supervisors see published documents only.
5. Feedback, a manager review queue, an audit trail and a per-run config snapshot.
6. Analytics: KPIs, trend, recurring issues, documentation gaps, drill-down and CSV export. Diagnostics page.
7. 29 pytest tests and a 32-case golden eval set with a repeatable runner.

**Built (v2)**
8. Router agent, three specialist agents with a read-only search tool, and a synthesizer agent, on a provider-agnostic LLM interface (OpenAI `gpt-4o-mini` first).
9. Supervised orchestration: stage order, parallel specialists, step and token caps, timeout, and automatic fallback to the v1 pipeline.
10. Agent trace (per step: agent, model, tokens, latency, status) in the response, the logs and the Diagnostics page.
11. Mode comparison in the eval runner (`python -m evals.run --compare`). Paraphrase eval cases and the formal live run are owned by the tests-and-evals session; results not yet reported here.

## 5. Out of scope (this prototype)

- Real authentication or SSO (a role selector is used instead).
- PDF/scanned document ingestion. Multiple languages and voice.
- CMMS or work-order integration. Cloud deployment.
- Long-term agent memory, and any agent that can write or publish.
- Sending real plant documents to an external LLM (needs a data-handling review).

## 6. Assumptions and success criteria

**Assumptions (illustrative):** 1 plant, ~40 supervisors, ~300 questions/day, 18 synthetic documents (~70 sections), Markdown with `## ` headings, English only, tablet or desktop browser.

| Criterion | Target | v1 result (measured, mock LLM) | v2 result (live LLM, 9-question quick check, not a full evaluation) |
|---|---|---|---|
| Routing accuracy | ≥ 90% | 100% (20/20) | not formally measured |
| Correct document cited | ≥ 85% | 100% | 7 of 9 answered with cited sources; correctness not formally scored |
| Abstains when not in docs | 100% | 100% (5/5) | off-topic question correctly refused (1/1); 1 vague in-scope question wrongly refused instead of a follow-up |
| Safety procedure included for hazards | 100% | 100% (5/5) | not formally measured; some answers add extra lockout steps (wordy but safe) |
| Draft-document leaks | 0 | 0 | not formally measured |
| Paraphrased questions routed correctly | ≥ 80% | n/a (rules can't) | not formally measured (paraphrases such as "the belt on C3 is stuck" were answered in the quick check) |
| p95 latency | < 8 s agent mode | ~1 ms (mock pipeline) | p95 not measured; average 7.2 s, slowest 11.3 s, so slow hazard questions miss the goal |
| Automated tests | all pass | 29/29 | to extend |

> The v1 pass rate (32/32) checks **pipeline wiring**, not AI quality. The mock is extractive and was written alongside the golden set. The v2 column is an informal quick check; formal live numbers will replace it once the separate evaluation run reports.

## 7. Roadmap

- **v1 (built):** local, single plant, rule-based pipeline, mock LLM, citations and approvals from day one.
- **v2 (built):** LLM agents for routing, research and answers; agent trace; fallback to v1; Streamlit UI. Live quality checked informally only.
- **Next:** real documents from one plant line, sign-in, faster answers, a second AI check on answers.
- **Later:** PDF ingestion, hybrid search, manager insights agent, CMMS integration, multi-plant rollout, online evaluation from feedback.
