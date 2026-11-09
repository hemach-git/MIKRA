"""Agent runner: bounded tool loop, schema validation with correction retry, per-step trace."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Callable, Type

from pydantic import BaseModel, ValidationError

from app.models.schemas import AgentStep
from app.services import llm
from app.services.guardrails import mask_pii


class AgentError(Exception):
    """Raised when an agent cannot produce a valid result within its limits (orchestrator falls back)."""


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    fn: Callable[..., str]

    def spec(self) -> dict:
        return {"type": "function", "function": {"name": self.name, "description": self.description,
                                                 "parameters": self.parameters}}


def _extract_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        raise ValueError("no JSON object in reply")
    return json.loads(m.group(0))


def run_agent(name: str, system: str, user: str, *, model: str, max_tokens: int, max_steps: int,
              schema: Type[BaseModel], tools: list[Tool] | None = None) -> tuple[BaseModel, list[AgentStep]]:
    """Run one agent. Steps are capped; the last step never offers tools so the agent must answer."""
    messages: list[dict] = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    by_name = {t.name: t for t in (tools or [])}
    steps: list[AgentStep] = []

    for i in range(max_steps):
        last = i == max_steps - 1
        offer = [t.spec() for t in by_name.values()] if (by_name and not last) else None
        try:
            res = llm.chat(messages, model=model, tools=offer, json_mode=offer is None, max_tokens=max_tokens)
        except Exception as e:
            steps.append(AgentStep(agent=name, kind="llm", model=model, status="error",
                                   summary=f"LLM call failed: {type(e).__name__}"))
            raise AgentError(f"{name}: LLM call failed ({type(e).__name__})") from e
        steps.append(AgentStep(agent=name, kind="llm", model=res.model or model, tokens_in=res.tokens_in,
                               tokens_out=res.tokens_out, latency_ms=res.latency_ms,
                               summary="requested tools: " + ", ".join(tc.name for tc in res.tool_calls)
                               if res.tool_calls else "returned an answer"))
        if res.tool_calls:
            messages.append({"role": "assistant", "content": res.text or None, "tool_calls": [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)}} for tc in res.tool_calls]})
            for tc in res.tool_calls:
                tool = by_name.get(tc.name)
                try:
                    out = tool.fn(**tc.arguments) if tool else f"Unknown tool {tc.name}."
                    status = "ok" if tool else "error"
                except Exception as e:  # bad arguments etc: report to the model, don't crash
                    out, status = f"Tool error: {type(e).__name__}", "error"
                steps.append(AgentStep(agent=name, kind="tool", name=tc.name, status=status,
                                       summary=mask_pii(json.dumps(tc.arguments))[:120]))
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": out})
            continue
        try:
            return schema.model_validate(_extract_json(res.text)), steps
        except (ValueError, ValidationError, json.JSONDecodeError) as e:
            steps[-1].status, steps[-1].summary = "error", f"invalid output: {type(e).__name__}"
            messages.append({"role": "assistant", "content": res.text})
            messages.append({"role": "user", "content": "Your reply was not valid JSON for the required format. "
                                                         "Return ONLY the JSON object."})
    raise AgentError(f"{name}: no valid answer within {max_steps} steps")
