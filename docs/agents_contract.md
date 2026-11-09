# Agent interface contract (v2)

Agreed **before** the sessions split. The Main session implements these. The Tests + evals session codes against them using a fake LLM. The Frontend session only sees `AskResponse` (`mode`, `agent_trace`).

## File ownership

| Session | Files |
|---|---|
| Main | `app/services/llm.py`, `app/services/workflow.py`, `app/services/router.py`, `app/agents/*`, `config.yaml`, `requirements.txt` |
| Frontend | `app/main.py`, `app/pages/*`, `app/ui/*`, `.streamlit/*` |
| Tests + evals | `tests/*`, `evals/*` |
| Docs (done) | `docs/*`, `README.md`, `scripts/*` |

Only the Main session commits.

## LLM adapter (`app/services/llm.py`)

```python
class ToolCall(BaseModel): id: str; name: str; arguments: dict
class ChatResult(BaseModel):
    text: str; tool_calls: list[ToolCall]; tokens_in: int; tokens_out: int; model: str; latency_ms: float

def chat(messages: list[dict], *, model: str, tools: list[dict] | None = None,
         response_schema: dict | None = None, max_tokens: int = 700, temperature: float = 0.0) -> ChatResult
```

- Providers: `openai`, `anthropic`, `mock` (selected by `LLM_PROVIDER`).
- **Tests replace `llm.chat` with a scripted fake** (`monkeypatch.setattr(llm, "chat", fake)`). No network in unit tests.

## Agents (`app/agents/`)

```python
# base.py
def run_agent(name: str, system: str, user: str, *, tools: list | None, model: str,
              max_steps: int, schema: type[BaseModel]) -> tuple[BaseModel, list[AgentStep]]
    # tool loop with step cap, schema validation + 1 retry; raises AgentError on failure

# router_agent.py
class RouterPlan(BaseModel):
    categories: list[Category]; confidence: float; hazard: bool
    equipment: str | None; queries: dict[str, str]; clarify: str | None
def plan(question: str) -> tuple[RouterPlan, list[AgentStep]]

# specialists.py
class Finding(BaseModel): claim: str; citation_ids: list[str]
class Findings(BaseModel): category: Category; findings: list[Finding]; abstain: bool
def research(category: str, question: str, search_query: str) -> tuple[Findings, list[AgentStep]]
    # tools: search_docs(query, top_k), read_section(chunk_id); both limited to `category`, published only

# synthesizer.py
def synthesize(question: str, plan: RouterPlan, findings: list[Findings]) -> tuple[LLMAnswer, list[AgentStep]]

# orchestrator.py
def answer(question: str, role: str) -> OrchestratorResult   # chosen categories, LLMAnswer, hits, trace, used_fallback
```

## Orchestrator rules (code, not model)

1. Hazard = keyword rules **OR** `RouterPlan.hazard`. If true, the Safety specialist always runs.
2. Specialists run in parallel, one per routed category (max 3).
3. A specialist can only see chunk ids returned by its own `search_docs` (published, own category).
4. Grounding check: every `citation_id` in the final answer must be a retrieved chunk. Otherwise drop it, and abstain if none remain.
5. Any `AgentError`, timeout (25 s) or token-budget breach → fall back to the rule-based pipeline and set `used_fallback=True`.
6. `agents.mode: pipeline` skips agents entirely (the v1 behaviour).
7. `RouterPlan.clarify` set and confidence low → return `status="abstained"` with the clarifying question in `abstain_reason` (the UI shows it).

## Response additions (`AskResponse`, already in `schemas.py`)

- `mode`: `"pipeline"` or `"multi_agent"`.
- `agent_trace`: list of `AgentStep` (seq, agent, kind, name, model, tokens_in, tokens_out, latency_ms, status, summary).
