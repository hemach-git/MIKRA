# MIKRA: Scope Document

**Project:** MIKRA (Manufacturing Intelligent Knowledge Routing Assistant)
**Client problem:** A plant operator wants floor supervisors to get answers from the right documentation (safety procedures, maintenance manuals or quality control standards), routed automatically and answered accurately.
**Engagement:** 2.5-hour prototype, local deployment only, **synthetic data**.

## 1. Business problem

Floor supervisors resolve issues during live production: jams, alarms, out-of-spec parts, PPE questions. Today they look through three separate binders. That causes:
- **Downtime:** minutes lost per issue searching for the right procedure.
- **Safety risk:** a maintenance fix done without the matching lockout procedure.
- **Quality escapes:** using an outdated spec, or a draft spec that was never approved.
- **No visibility:** managers can't see which issues keep recurring on the floor.

## 2. Users

| User | Needs | What MIKRA gives them |
|---|---|---|
| Floor Supervisor (primary) | Fast, reliable answers during operations | One question box; routed, cited answer with steps; safety warnings first; "not found" instead of a guess |
| Plant Operator / Manager (admin) | Keep documentation current; see recurring issues | Draft → approve → publish workflow; review queue for flagged answers; analytics of recurring issues and documentation gaps |

## 3. In scope (delivered)

1. Question routing to Safety, Maintenance or Quality (more than one where needed). Explainable rules + classifier.
2. **Safety override:** hazard-related tasks always include the safety procedure.
3. Grounded answers with numbered steps, safety notes, citations (document, version, section) and a confidence level.
4. **Abstain** when the documents don't cover the question.
5. Guardrails:
   - Prompt-injection and safety-bypass requests are blocked.
   - Emergency detection shows the emergency contact banner.
   - PII is masked in storage and logs.
   - Document text is treated as untrusted.
6. Document lifecycle: draft → manager approval → published (previous version retired). Supervisors only see published documents.
7. Feedback (thumbs up / flag wrong). Flagged answers go to a manager review queue with an approve/reject decision.
8. Audit trail (who, what, when, decision, model, request_id) and a per-run config snapshot.
9. Analytics:
   - KPIs: questions, answer rate, safety-routed %, p95 latency, helpful %.
   - Daily trend, recurring issues by equipment, documentation gaps, most-cited documents.
   - Drill-down and CSV export.
10. Diagnostics: health, config, recent requests with stage timings, eval summary.
11. Tests (29 pytest) and a golden eval set (32 cases) with a repeatable runner.

## 4. Out of scope (this prototype)

- Live LLM. The `anthropic` provider is wired but **not yet validated**; mock only, by request. The live LLM eval is **deferred**.
- Real authentication or SSO (a role selector is used instead).
- PDF/scanned document ingestion. Multiple languages and voice.
- CMMS or work-order integration. Cloud deployment.

## 5. Assumptions (illustrative)

- 1 plant, ~40 supervisors, ~300 questions/day.
- 18 synthetic documents (6 per category), ~70 sections.
- Documents are written in Markdown with `## ` section headings.
- English only. Tablet or desktop browser on the floor.

## 6. Success criteria and results

| Criterion | Target | Result (mock LLM, synthetic data) |
|---|---|---|
| Routing accuracy (golden set) | ≥ 90% | **100%** (20/20 routed cases) |
| Correct document cited | ≥ 85% | **100%** |
| Abstains when not in docs | 100% | **100%** (5/5) |
| Safety procedure included for hazards | 100% | **100%** (5/5) |
| Draft-document leaks | 0 | **0** |
| p95 latency | < 5 s | **~1 ms** (mock; a live LLM will add ~1–3 s) |
| Automated tests | all pass | **29/29** |

> The eval pass rate (32/32) checks the **pipeline wiring** (routing, retrieval, guardrails, grounding), not live LLM answer quality. The mock is extractive and was written alongside the golden set.

## 7. Roadmap

- **v0 (this prototype):** local, single plant, mock LLM, synthetic data, citations and approvals from day one.
- **v1:**
  - Connect the Claude API and run the live eval.
  - SSO with role-based access.
  - PDF ingestion with hybrid (keyword + vector) search and a reranker.
  - Tablet UI tuned for the floor; multiple languages.
  - Eval in CI.
- **v2:**
  - CMMS integration (auto-suggest work orders for recurring issues).
  - Multi-plant rollout.
  - Online evaluation from user feedback.
