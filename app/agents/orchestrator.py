"""Orchestrator: plain code that owns stage order, hazard override, parallelism, caps and fallback.

Agents propose; code decides. Any AgentError / timeout / budget breach raises to the caller, which falls back
to the rule-based pipeline.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout

from pydantic import BaseModel, Field

from app.agents import router_agent, specialists, synthesizer
from app.agents.base import AgentError
from app.config import get_config
from app.models.schemas import CATEGORIES, AgentStep, LLMAnswer, RouteDecision
from app.services import retriever
from app.services import router as rules_router


class OrchestratorResult(BaseModel):
    decision: RouteDecision
    answer: LLMAnswer
    hits: list[dict] = Field(default_factory=list)
    trace: list[AgentStep] = Field(default_factory=list)
    tokens_in: int = 0
    tokens_out: int = 0
    equipment: str | None = None
    clarify: str | None = None


def _finish_trace(trace: list[AgentStep]) -> tuple[int, int]:
    for i, s in enumerate(trace, 1):
        s.seq = i
    return sum(s.tokens_in for s in trace), sum(s.tokens_out for s in trace)


def _check_budget(trace: list[AgentStep], budget: int) -> None:
    used = sum(s.tokens_in + s.tokens_out for s in trace)
    if used > budget:
        raise AgentError(f"token budget exceeded ({used} > {budget})")


def answer(question: str, emergency: bool = False) -> OrchestratorResult:
    cfg = get_config()
    acfg = cfg["agents"]
    trace: list[AgentStep] = []

    # 1. Router agent
    plan, steps = router_agent.plan(question)
    trace += steps
    _check_budget(trace, acfg["token_budget"])

    # 2. Hazard override (CODE): keyword rules OR router flag OR emergency -> Safety always runs
    hazard = rules_router.hazard_flag(question) or plan.hazard or emergency
    cats = list(plan.categories)
    broad = False
    if not cats and plan.confidence > 0:
        cats, broad = list(CATEGORIES), True
    if hazard and "safety" not in cats:
        cats.append("safety")
        trace.append(AgentStep(agent="orchestrator", kind="guard", name="hazard_override",
                               summary="Safety specialist added (hazard detected)"))
    if emergency and "safety" in cats:
        cats.remove("safety")
        cats.insert(0, "safety")

    equipment = plan.equipment if plan.equipment in cfg["equipment"] else None
    clarify_needed = bool(plan.clarify) and plan.confidence < acfg["min_clarify_confidence"] and not hazard

    def _decision(cs: list[str]) -> RouteDecision:
        primary = cs[0] if cs else "maintenance"
        return RouteDecision(categories=cs or [primary], primary=primary, confidence=plan.confidence,
                             safety_flag=hazard, broad_search=broad, method="agent:router",
                             scores={c: plan.confidence for c in cs}, reason=plan.reason or "Routed by the router agent.")

    if clarify_needed:
        tin, tout = _finish_trace(trace)
        return OrchestratorResult(decision=_decision(cats), answer=LLMAnswer(answer="", abstain=True),
                                  trace=trace, tokens_in=tin, tokens_out=tout, equipment=equipment,
                                  clarify=plan.clarify)
    if not cats:   # router says: not a plant-operations question
        tin, tout = _finish_trace(trace)
        return OrchestratorResult(decision=_decision(list(CATEGORIES)), answer=LLMAnswer(answer="", abstain=True),
                                  trace=trace, tokens_in=tin, tokens_out=tout, equipment=equipment)

    # 3. Specialists in parallel (each: own category only, published only, max steps)
    def run(cat: str):
        q = plan.queries.get(cat) or question
        if emergency and cat == "safety":
            q += " emergency procedure"
        return specialists.research(cat, question, q)

    found: list[specialists.Findings] = []
    with ThreadPoolExecutor(max_workers=len(cats)) as pool:
        futures = {c: pool.submit(run, c) for c in cats}
        for c, fut in futures.items():
            try:
                f, st = fut.result(timeout=acfg["timeout_s"])
            except FutureTimeout as e:
                raise AgentError(f"{c} specialist timed out") from e
            trace += st
            found.append(f)
    _check_budget(trace, acfg["token_budget"])

    # 3b. Safety evidence guarantee (CODE): a hazard task must carry a cited safety section even if the safety
    #     specialist returned nothing. Evidence is a real, published section, so it is grounded by construction.
    if hazard:
        sf = next((f for f in found if f.category == "safety"), None)
        if sf is None or not sf.findings:
            qs = (plan.queries.get("safety") or "") + " " + question
            top = retriever.search(qs, ["safety"], top_k=1)
            if top:
                h = top[0]
                warn = [ln.replace("WARNING:", "").strip() for ln in h["text"].splitlines() if ln.startswith("WARNING")]
                claim = warn[0] if warn else h["text"].splitlines()[0][:300]
                added = specialists.Findings(category="safety", abstain=False, chunks=[h],
                                             findings=[specialists.Finding(claim=claim, citation_ids=[h["chunk_id"]])])
                found = [f for f in found if f.category != "safety"] + [added]
                trace.append(AgentStep(agent="orchestrator", kind="guard", name="safety_evidence_added",
                                       summary=f"Added {h['doc_key']} - {h['section']} (safety specialist found nothing)"))

    # 4. Synthesizer (skipped when no specialist found anything: abstain)
    useful = [f for f in found if f.findings]
    if not useful:
        tin, tout = _finish_trace(trace)
        return OrchestratorResult(decision=_decision(cats), answer=LLMAnswer(answer="", abstain=True),
                                  trace=trace, tokens_in=tin, tokens_out=tout, equipment=equipment)
    ans, st, hits = synthesizer.synthesize(question, plan, useful, hazard)
    trace += st
    _check_budget(trace, acfg["token_budget"])
    tin, tout = _finish_trace(trace)
    return OrchestratorResult(decision=_decision(cats), answer=ans, hits=hits, trace=trace,
                              tokens_in=tin, tokens_out=tout, equipment=equipment)
