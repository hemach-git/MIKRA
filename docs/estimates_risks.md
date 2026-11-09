# MIKRA: Estimates and Risk Register

## 1. Effort estimates

| Phase | Prototype (actual, AI-assisted) | Pilot v1 (estimate) |
|---|---|---|
| Design + plan | 20 min | 1 week |
| Backend: routing, retrieval, answer pipeline | 40 min | 2 weeks |
| Guardrails, governance, audit, analytics | 25 min | 2 weeks |
| Frontend (parallel session) | ~60 min | 2 weeks |
| Tests + evals | 20 min | 1 week (+ live LLM eval, judge calibration) |
| Docs + slide + push | 20 min | — |
| Real document ingestion (PDF, OCR), SSO, deployment | — | 3–4 weeks |
| **Total** | **~2.5 h** | **~10–12 weeks, 2–3 engineers** |

## 2. Run-cost estimate (illustrative, live LLM)

- ~300 questions/day × ~2,500 input + ~400 output tokens per question, about 0.9M tokens/day.
- At typical mid-tier model pricing that is **tens of dollars per month** for one plant.
- Cost levers:
  - Cache answers to frequent questions.
  - Route classification to a small model.
  - Cap the context at 8 sections.

## 3. Risk register

| # | Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| R1 | Safety question routed only to Maintenance | Low | **High** | Hazard keyword override forces the Safety source in; safety-inclusion recall eval at 100%; the safety note is shown first | EHS + Eng |
| R2 | Confident wrong answer (hallucination) | Med (live LLM) | High | Answers only from retrieved sections; grounding check (citations must be retrieved); abstain on weak evidence; human feedback loop | Eng |
| R3 | Outdated or unapproved document used | Med | High | Published-only retrieval; draft → approve workflow; old version retired automatically; draft-leak eval at 0 | Quality Mgr |
| R4 | Prompt injection via question or document text | Med | Med | Injection and bypass patterns blocked; document text delimited as untrusted; document scan flags embedded instructions for the reviewer | Eng |
| R5 | Supervisor relies on MIKRA in an emergency | Low | **High** | Emergency keywords show the "call ext. 5555" banner first; emergency SOP cited | EHS |
| R6 | Keyword retrieval misses synonyms (e.g. "stuck" vs "jam") | Med | Med | v1: hybrid vector search plus a synonym list; documentation-gaps report shows misses | Eng |
| R7 | Live LLM not yet validated (mock only) | Certain (today) | Med | Mock provider makes the demo deterministic; run `evals.run` with `LLM_PROVIDER=anthropic` before the pilot | Eng |
| R8 | PII in questions (names, phones) | Med | Med | Masked before storage and logging | Eng |
| R9 | Low adoption on the floor | Med | High | Answers in under 5 s, plain English, tablet UI; track usage and helpful % in analytics | Plant Mgr |
| R10 | Synthetic data differs from real binders | Certain | Med | Pilot with 2–3 real documents per category; re-tune thresholds; re-run the golden set | Eng + SMEs |

## 4. Assumptions and limitations

- All documents, queries and feedback are **synthetic** (`is_synthetic=1`).
- The role selector is not authentication.
- The LLM is mock-only. Answers are extractive quotes of the best sections, so they are reliable but not conversational.
- BM25 keyword retrieval is suited to ~100 sections; larger corpora need hybrid search.
- SQLite runs single-node and locally.
