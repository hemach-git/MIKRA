# S2: Tests + evals session

- **Session id:** `4c541cee-6ce4-4287-95b7-9037ae70342c`
- **Title (auto):** Agent tests and evals runner
- **Time span:** 2026-11-09 16:55 UTC → 2026-11-09 17:16 UTC
- **Counts:** 3 user messages · 3 assistant turns · 26 tool calls
- **Not included:** harness system reminders, internal thinking, raw metadata. Tool results are truncated to 350 chars.
- **Redaction:** key-like strings are replaced with `[REDACTED-KEY]`.

---

### 🧑 User — 2026-11-09 16:55 UTC

<pasted_content id="86dd">
Read docs/tests_evals_brief.md, docs/agents_contract.md and docs/design.md first.
You own ONLY: tests/* and evals/*. Do NOT edit app/*, config.yaml, docs/*, scripts/*.
Do NOT run git commit or git push; the main session commits.

Current state (the agents are built and already ran live):
- .env has LLM_PROVIDER=openai and a working OPENAI_API_KEY (gpt-4o-mini). Never print or log the key.
- Agent code is in app/agents/*; scripts/agent_smoke.py is a working example of a scripted fake LLM
  (monkeypatch llm.chat and llm.provider -> "openai"). Reuse its patterns in tests/fakes.py.
- tests/conftest.py forces LLM_PROVIDER=mock; keep that for existing tests. New agent tests must switch agents on explicitly.
- IMPORTANT: evals/run.py currently follows .env, so it would now run live agents. Add --mode pipeline|multi_agent;
  pipeline must force LLM_PROVIDER=mock. Default to pipeline so a plain run stays free and deterministic.

Tasks, in order:
1. tests/fakes.py (scripted chat per agent, with failure injection) and tests/test_agents.py as in the brief.
   Also cover: citation ids wrapped in tags (e.g. <chunk id="X#s1">) are cleaned by base.clean_id; fake ids still dropped;
   hazard override adds Safety; fallback on API error; 3-step cap; agents.mode=pipeline gives an empty trace.
2. Add ~10 paraphrase cases to evals/golden.jsonl (ids A01..A10, "modes": ["multi_agent"]).
   Also add 3 hazard cases that REQUIRE a safety citation in multi_agent mode (field expect_safety_citation).
3. evals/run.py: --mode, --compare, record agent_trace summary, LLM calls, tokens and estimated cost per case,
   write evals/results/latest_<mode>.json. Keep the mock-provider warning; print a banner for live runs.
4. Run: python -m pytest -q, then python -m evals.run --mode pipeline, then python -m evals.run --mode multi_agent (live, ~40 cases, a few cents).
5. Report REAL numbers, failures included, and for each failing live case say whether it is a wrong route, a missing citation,
   a wrong or irrelevant safety note, or an abstain. Do not edit the golden set to make a model pass.
Known live findings to check against: hazard questions take 8-16 s and 6-8 LLM calls; one case surfaced an irrelevant
safety note; one answer mentioned lockout without a safety citation. Tell me if your evals reproduce these.
</pasted_content id="86dd">


### 🤖 Assistant — 2026-11-09 16:56 UTC

🤖 SWITCH MODEL: Run `/model sonnet` before we begin. This is test and eval work across several files, which fits the Sonnet tier. I'll go ahead now because this session is non-interactive.

- 🔧 **Glob**: */docs/tests_evals_brief.md in .

  ↳ _result:_ `Ripgrep search timed out after 20 seconds. The search may have matched files but did not complete in time. Try searching a more specific path or pattern.`
- 🔧 **Read**: C:\Users\Chepuri\.claude\projects\C--Users-Chepuri\memory\project-mikra-doc-router.md

  ↳ _result:_ `1	--- ⏎ 2	name: project-mikra-doc-router ⏎ 3	description: "MIKRA manufacturing doc-routing Q&A prototype (2.5h FDE challenge) - status, repo, open items" ⏎ 4	metadata: ⏎ 5	  node_type: memory ⏎ 6	  type: project ⏎ 7	  originSessionId: dae13766-114d-4f2b-87f3-b094901f5e2c ⏎ 8	  modified: 2026-11-09T16:06:22.876Z ⏎ 9	--- ⏎ 10	 ⏎ 11	MIKRA routes floor ... [+721 chars truncated]`
- 🔧 **Bash**: cd /c/Users/Chepuri/mfg-doc-router && ls docs tests evals app app/agents scripts && cat docs/tests_evals_brief.md docs/agents_contract.md

  ↳ _result:_ `app: ⏎ __init__.py ⏎ __pycache__ ⏎ agents ⏎ config.py ⏎ data ⏎ main.py ⏎ models ⏎ observability ⏎ pages ⏎ services ⏎ ui ⏎  ⏎ app/agents: ⏎ __init__.py ⏎ __pycache__ ⏎ base.py ⏎ orchestrator.py ⏎ prompts.py ⏎ router_agent.py ⏎ specialists.py ⏎ synthesizer.py ⏎  ⏎ docs: ⏎ agents_contract.md ⏎ architecture.md ⏎ data_model.md ⏎ data_sources.md ⏎ design ... [+7476 chars truncated]`
- 🔧 **Bash**: cd /c/Users/Chepuri/mfg-doc-router && cat scripts/agent_smoke.py app/agents/*.py tests/conftest.py evals/run.py && head -5 evals/golden.jsonl && wc -l evals/gol ... [+28 chars truncated]

  ↳ _result:_ `<persisted-output> ⏎ Output too large (37.9KB). Full output saved to: C:\Users\Chepuri\.claude\projects\C--Users-Chepuri\4c541cee-6ce4-4287-95b7-9037ae70342c\tool-results\btc4fnj1k.txt ⏎  ⏎ Preview (first 2KB): ⏎ """Offline smoke test of the agent path with a scripted fake LLM (no key, no network): python scripts/agent_smoke.py""" ⏎ import json, o ... [+1945 chars truncated]`
- 🔧 **Read**: C:\Users\Chepuri\.claude\projects\C--Users-Chepuri\4c541cee-6ce4-4287-95b7-9037ae70342c\tool-results\btc4fnj1k.txt

  ↳ _result:_ `1	"""Offline smoke test of the agent path with a scripted fake LLM (no key, no network): python scripts/agent_smoke.py""" ⏎ 2	import json, os, re, sys, tempfile ⏎ 3	from pathlib import Path ⏎ 4	 ⏎ 5	tmp = Path(tempfile.mkdtemp(prefix="mikra-agent-")) ⏎ 6	os.environ.update(MIKRA_DB_PATH=str(tmp / "t.db"), MIKRA_LOG_DIR=str(tmp / "logs"), LLM_PROVIDE ... [+42676 chars truncated]`
- 🔧 **Bash**: cd /c/Users/Chepuri/mfg-doc-router && cat app/services/workflow.py app/config.py && sed -n 1,80p app/services/llm.py && grep -n "class AgentStep" -A 15 app/mode ... [+201 chars truncated]

  ↳ _result:_ `<persisted-output> ⏎ Output too large (28.7KB). Full output saved to: C:\Users\Chepuri\.claude\projects\C--Users-Chepuri\4c541cee-6ce4-4287-95b7-9037ae70342c\tool-results\brkanntqu.txt ⏎  ⏎ Preview (first 2KB): ⏎ """Core use case: supervisor asks -> guardrails -> route -> retrieve -> answer -> ground -> store -> audit. ⏎  ⏎ Fixed single-pass pipe ... [+1997 chars truncated]`
Still reading the workflow and LLM code; next I'll write the fakes and tests.

- 🔧 **Read**: C:\Users\Chepuri\.claude\projects\C--Users-Chepuri\4c541cee-6ce4-4287-95b7-9037ae70342c\tool-results\brkanntqu.txt

  ↳ _result:_ `60	def _validate_llm(raw: str) -> LLMAnswer: ⏎ 61	    m = re.search(r"\{.*\}", raw, re.S) ⏎ 62	    if not m: ⏎ 63	        raise ValueError("no JSON object in model output") ⏎ 64	    return LLMAnswer.model_validate(json.loads(m.group(0))) ⏎ 65	 ⏎ 66	 ⏎ 67	def _abstain_reason(hits: list[dict]) -> str: ⏎ 68	    rc = get_config()["retrieval"] ⏎ 69 ... [+29612 chars truncated]`
- 🔧 **Bash**: cd /c/Users/Chepuri/mfg-doc-router && sed -n 88,112p docs/design.md && grep -n "def chat\|def provider\|openai\|class ChatResult\|class ToolCall" app/services/l ... [+139 chars truncated]

  ↳ _result:_ `- **Human in the loop:** document publishing and flag review stay manager decisions. ⏎  ⏎ ## 5. Evals and observability ⏎  ⏎ **Golden set:** 32 cases today (15 positive, 5 multi-route, 5 negative, 7 edge). For v2, add about 10 **paraphrase cases** that keyword routing cannot pass, tagged `agent_only`, so they count only in agent mode. ⏎  ⏎ **Metric ... [+2110 chars truncated]`
- 🔧 **Bash**: cd /c/Users/Chepuri/mfg-doc-router && sed -n 25,46p app/services/router.py && sed -n 140,200p app/services/llm.py && ls app/data && grep -rhn "doc_key\|^## \|ti ... [+42 chars truncated]

  ↳ _result:_ `r"control chart", r"\bcpk\b", r"out of control", r"finish", r"orange peel", ⏎                 r"film thickness", r"porosity", r"undercut", r"accept", r"\bspec", r"measur", ⏎                 r"first article", r"bore", r"nugget", r"quarantine", r"dimension", r"run.? and sag", r"fish ?eye"], ⏎ } ⏎ # Hazard terms: work that may expose a person to energ ... [+3218 chars truncated]`
- 🔧 **Bash**: cd /c/Users/Chepuri/mfg-doc-router && ls app/data/corpus && grep -h "^#\|^doc_key\|^title" app/data/corpus/* | head -80

  ↳ _result:_ `drafts ⏎ maintenance ⏎ quality ⏎ safety ⏎ grep: app/data/corpus/drafts: Is a directory ⏎ grep: app/data/corpus/maintenance: Is a directory ⏎ grep: app/data/corpus/quality: Is a directory ⏎ grep: app/data/corpus/safety: Is a directory`
- 🔧 **Bash**: cd /c/Users/Chepuri/mfg-doc-router && ls app/data/corpus/* && grep -h "^## " app/data/corpus/*/*.md | head -80

  ↳ _result:_ `app/data/corpus/drafts: ⏎ QC-TORQ-01.md ⏎  ⏎ app/data/corpus/maintenance: ⏎ MM-CNC-04.md ⏎ MM-COMP-03.md ⏎ MM-CONV-02.md ⏎ MM-PM-06.md ⏎ MM-PRESS-01.md ⏎ MM-ROB-05.md ⏎  ⏎ app/data/corpus/quality: ⏎ QC-DIM-02.md ⏎ QC-NCR-03.md ⏎ QC-PAINT-05.md ⏎ QC-SPC-04.md ⏎ QC-TORQ-01.md ⏎ QC-WELD-06.md ⏎  ⏎ app/data/corpus/safety: ⏎ SOP-CHEM-03.md ⏎ SOP-EMR-02. ... [+1986 chars truncated]`
Writing fakes next. First I'll check the corpus wording so the paraphrase cases have real target documents.

- 🔧 **Bash**: cd /c/Users/Chepuri/mfg-doc-router/app/data/corpus && grep -il "respirator" */*.md; grep -il "orange peel" */*.md; grep -il "porosity" */*.md; grep -n "km/h\|sp ... [+162 chars truncated]

  ↳ _result:_ `safety/SOP-PPE-01.md ⏎ quality/QC-PAINT-05.md ⏎ quality/QC-WELD-06.md ⏎ 12:Maximum forklift speed is 8 km/h on the production floor. Pedestrians use marked walkways. Sound the horn at intersections and blind corners. ⏎ maintenance/MM-CONV-02.md:23:Repeated conveyor motor overload trips usually indicate a seized roller or over-tensioned belt. Check ... [+725 chars truncated]`
Now writing the golden-set additions and tests/fakes.py.

- 🔧 **Bash**: cd /c/Users/Chepuri/mfg-doc-router && tail -c 1 evals/golden.jsonl | od -c | head -1 && cat >> evals/golden.jsonl <<'EOF'
{"id": "A01", "type": "paraphrase", "m ... [+2893 chars truncated]

  ↳ _result:_ `0000000  \n ⏎ 45 evals/golden.jsonl`
- 🔧 **Write**: C:\Users\Chepuri\mfg-doc-router\tests\fakes.py (5893 chars)

  ↳ _result:_ `File created successfully at: C:\Users\Chepuri\mfg-doc-router\tests\fakes.py (file state is current in your context — no need to Read it back)`
Fakes written; now the agent tests.

- 🔧 **Write**: C:\Users\Chepuri\mfg-doc-router\tests\test_agents.py (12107 chars)

  ↳ _result:_ `File created successfully at: C:\Users\Chepuri\mfg-doc-router\tests\test_agents.py (file state is current in your context — no need to Read it back)`
- 🔧 **Bash**: cd /c/Users/Chepuri/mfg-doc-router && python -m pytest -q tests/test_agents.py 2>&1 | tail -40

  ↳ _result:_ `.........................                                                [100%] ⏎ 25 passed in 2.83s`
All 25 pass. Small tidy-up (move `import re` to the module top), then evals/run.py.

- 🔧 **Bash**: cd /c/Users/Chepuri/mfg-doc-router && python - <<'EOF'
p='tests/test_agents.py'; s=open(p,encoding='utf-8').read()
s=s.replace("            import re\n","").rep ... [+210 chars truncated]

  ↳ _result:_ `8:import re`
Now rewriting evals/run.py with `--mode`, `--compare`, per-case cost and trace, and failure classes.

- 🔧 **Write**: C:\Users\Chepuri\mfg-doc-router\evals\run.py (15249 chars)

  ↳ _result:_ `The file C:\Users\Chepuri\mfg-doc-router\evals\run.py has been updated successfully. (file state is current in your context — no need to Read it back)`
- 🔧 **Edit**: C:\Users\Chepuri\mfg-doc-router\evals\run.py

- 🔧 **Bash**: cd /c/Users/Chepuri/mfg-doc-router && python -m pytest -q 2>&1 | tail -5 && python -m evals.run --mode pipeline 2>&1 | tail -30

  ↳ _result:_ `The file C:\Users\Chepuri\mfg-doc-router\evals\run.py has been updated successfully. (file state is current in your context — no need to Read it back)`
  ↳ _result:_ `......................................................                   [100%] ⏎ 54 passed in 3.84s ⏎  ⏎ MIKRA eval [pipeline] - mock-extractive-v1  (32/32 passed, 100.0%, 13 skipped for this mode) ⏎   routing_accuracy           100.0 ⏎   citation_hit_rate          100.0 ⏎   abstain_correctness        100.0 ⏎   safety_inclusion_recall    10 ... [+696 chars truncated]`
Tests pass (54/54) and the pipeline eval passes (32/32). Starting the live multi_agent run now (45 cases, a few minutes).

- 🔧 **Bash**: cd /c/Users/Chepuri/mfg-doc-router && python -m evals.run --mode multi_agent > "C:/Users/Chepuri/AppData/Local/Temp/claude/85c5701e75a1ca0f/4c541cee-6ce4-4287-9 ... [+47 chars truncated]

  ↳ _result:_ `Command running in background with ID: bpzl7g2cd. Output is being written to: C:\Users\Chepuri\AppData\Local\Temp\claude\85c5701e75a1ca0f\4c541cee-6ce4-4287-95b7-9037ae70342c\tasks\bpzl7g2cd.output. You will be notified when it completes — do not poll that file or sleep while waiting. Read the file only if the user asks for progress, or if you need ... [+206 chars truncated]`
The live run is going in the background. I'll report once it finishes.

- 🔧 **Bash**: echo waiting

  ↳ _result:_ `waiting`
The live multi_agent eval is still running in the background. When it finishes I'll report the real numbers, sorting each failure into wrong route, missing citation, wrong or irrelevant safety note, or abstain.


### 🧑 User — 2026-11-09 17:13 UTC

I verified the Q on FrontEnd-"How do I clear a jam on Conveyor C3?"  My observations are 1) The Match Confidence level decreased when I asked the same question twice, dropped from 100% to 90%.  2) How the confidence % is calculated 3) Where can I see the end-to-end tracing ?


### 🤖 Assistant — 2026-11-09 17:13 UTC

- 🔧 **Grep**: (?i)match confidence|agent_trace|confidence in C:\Users\Chepuri\mfg-doc-router\app

  ↳ _result:_ `No matches found`
- 🔧 **Bash**: cd /c/Users/Chepuri/mfg-doc-router && grep -rn -i "match\|confidence\|agent_trace\|trace" app/main.py app/pages app/ui app/observability --include=*.py | grep - ... [+83 chars truncated]

  ↳ _result:_ `app/pages/analytics.py:29:    st.info("No questions match these filters.") ⏎ app/pages/ask.py:21:CONF_LABELS = {"high": "High confidence", "medium": "Medium confidence", "low": "Low confidence"} ⏎ app/pages/ask.py:32:        except Exception as exc:  # backend should not raise, but never show a stack trace to the floor ⏎ app/pages/ask.py:50: ... [+2095 chars truncated]`
- 🔧 **Bash**: cd /c/Users/Chepuri/mfg-doc-router && sed -n 40,55p app/pages/ask.py && sed -n 113,135p app/pages/ask.py && grep -n -i "trace\|log" app/pages/diagnostics.py | h ... [+63 chars truncated]

  ↳ _result:_ `def render_route(resp) -> None: ⏎     r = resp.route ⏎     if not r: ⏎         return ⏎     chips = "" ⏎     for cat in r.categories: ⏎         label = CAT_LABELS.get(cat, cat.title()) ⏎         if cat == r.primary: ⏎             label += f" - {round(r.confidence * 100)}% match" ⏎         else: ⏎             label += " - also checked" ⏎         chi ... [+2139 chars truncated]`
Short version: the drop from 100% to 90% isn't a bug. In agent mode, "match %" is a score the router model gives itself, and gpt-4o-mini gives slightly different scores on repeat runs even at temperature 0. The live eval is still running in the background.

**1) Why it dropped from 100% to 90%**
- The "% match" chip is `round(route.confidence × 100)`, shown only on the primary category ([ask.py:50](mfg-doc-router/app/pages/ask.py#L50)).
- In agent mode, `route.confidence` is just the `confidence` number the router agent returns in its JSON ([orchestrator.py](mfg-doc-router/app/agents/orchestrator.py), `_decision()`). Nothing in the code calculates it.
- So 1.0 one time and 0.9 the next is normal variation. The routing (Maintenance plus Safety), the citations and the answer can stay the same.
- In plain terms, it's the model's own guess, not a calibrated probability. Showing "92%" makes it look more precise than it is.

**2) How the % is calculated**

| Mode | Source of "% match" |
|---|---|
| multi_agent (live, what you saw) | Router LLM's self-reported `confidence` (0 to 1) |
| pipeline / fallback | `0.5 × keyword-rule score + 0.5 × classifier score` for the top category ([router.py:52-75](mfg-doc-router/app/services/router.py#L52-L75)). The rule score is `hits / (hits + 1)`; the mock classifier is `BM25 / (BM25 + 6)`. This one is deterministic. |

- The separate "High / Medium / Low confidence" pill is a different value: the confidence the synthesizer gives its answer. The code forces it to "low" if the route confidence is under 0.4.
- Suggestion for the main session, since I don't own `app/*`: show a band (High/Medium) instead of a %, or base the % on the retrieval evidence.

**3) Where to see end-to-end tracing**
- **Ask page:** open the expander **"How MIKRA answered"** under the answer. It shows each step with its agent, model, tokens, ms and status, plus a badge for "AI agents" or "Rule-based / backup method".
- **Diagnostics page:** shows the last 100 log events from `logs/app.jsonl`. Each `ask` event has the full `agent_steps`, stage timings, tokens, mode, flags and `request_id`.
- **Raw log file:** `logs/app.jsonl`. Use `request_id` to join the `ask` event to any `agent_fallback` event.
- **Audit table** (database): one row per question, with categories, citations, config hash, mode and prompt version.
- **Evals:** `evals/results/latest_multi_agent.json` will have the full trace for every case once the live run finishes.

The UI table leaves out each step's `summary` and tool-call details (for example "sources=[...] hazard=True", "3 cited findings"). They are in the logs and eval JSON only. Adding them to the expander would be a quick front-end change.


### 🧑 User — 2026-11-09 17:16 UTC

There is no UI page created to see the trace my self. right?


### 🤖 Assistant — 2026-11-09 17:16 UTC

- 🔧 **Bash**: cd /c/Users/Chepuri/mfg-doc-router && sed -n 40,70p app/pages/diagnostics.py

  ↳ _result:_ `st.json(redact(get_config())) ⏎  ⏎ st.subheader("Recent requests") ⏎ logs = recent_logs(100) ⏎ if not logs: ⏎     st.info("No log events yet. Ask a question first.") ⏎ else: ⏎     errors = sum(1 for e in logs if e.get("status") == "error" or e.get("error")) ⏎     c1, c2 = st.columns(2) ⏎     c1.metric("Events shown", len(logs)) ⏎     c2.metric("Err ... [+1065 chars truncated]`
Right, there's no page for browsing traces. What exists today:

- **Ask page:** the "How MIKRA answered" expander shows the step table, but only for the answer you just got. Once you ask something else it's gone, and past requests can't be looked up.
- **Diagnostics → "Recent requests":** one row per request with time, request_id, status, latency, tokens and the time spent in each stage. It doesn't show the agent steps, even though they're saved in `logs/app.jsonl` (`agent_steps`).

So the full per-request trace is only in the log file and the eval JSON.

Two more things:
- I can't build the page myself: `app/pages/*` belongs to the Frontend session, and I'm limited to `tests/*` and `evals/*`. A small "Trace" view would cover it: pick a request_id from Recent requests, then show its agent steps (agent, kind, tool, model, tokens, ms, status, summary), any guards (hazard override, safety evidence added) and fallback events. I can write a short brief for the Frontend session if you want.
- The Diagnostics "Evaluation results" panel reads `latest.json`. With my change to `evals/run.py`, that file now holds whichever mode ran last. Once the live run finishes it will show multi_agent numbers. The page could read `latest_pipeline.json` and `latest_multi_agent.json` separately; that's another Frontend change.

The live eval is still running. I'll report when it's done.
