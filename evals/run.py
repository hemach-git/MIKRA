"""Repeatable eval runner:  python -m evals.run

Runs the golden set against a fresh, isolated, seeded DB and writes evals/results/latest.json + a timestamped copy.
NOTE: with LLM_PROVIDER=mock the pass rate checks the PIPELINE WIRING (routing, retrieval, guardrails,
grounding), not real LLM answer quality - the mock is extractive and was written alongside this golden set.
"""
from __future__ import annotations

import json
import os
import statistics
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def check(case: dict, r) -> list[str]:
    fails = []
    if r.status != case["expect_status"]:
        fails.append(f"status {r.status} != {case['expect_status']}")
    if "expect_primary" in case and (not r.route or r.route.primary != case["expect_primary"]):
        fails.append(f"primary {r.route.primary if r.route else None} != {case['expect_primary']}")
    for c in case.get("expect_categories_include", []):
        if not r.route or c not in r.route.categories:
            fails.append(f"category {c} not routed")
    if "expect_cited_doc" in case and case["expect_cited_doc"] not in [c.doc_key for c in r.citations]:
        fails.append(f"{case['expect_cited_doc']} not cited ({[c.doc_key for c in r.citations]})")
    if case.get("expect_safety_citation") and not any(c.category == "safety" for c in r.citations):
        fails.append("no safety citation")
    if "expect_answer_contains" in case and case["expect_answer_contains"] not in r.answer:
        fails.append(f"answer missing '{case['expect_answer_contains']}'")
    if "expect_answer_not_contains" in case and case["expect_answer_not_contains"] in r.answer:
        fails.append(f"answer contains forbidden '{case['expect_answer_not_contains']}'")
    if case.get("expect_no_draft") and any(c.doc_id.endswith("-v2") for c in r.citations):
        fails.append("DRAFT document leaked")
    if "expect_emergency" in case and r.emergency != case["expect_emergency"]:
        fails.append("emergency flag mismatch")
    if "expect_masked" in case and case["expect_masked"] in r.question:
        fails.append("PII not masked")
    return fails


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="mikra-eval-"))
    os.environ["MIKRA_DB_PATH"] = str(tmp / "eval.db")
    os.environ["MIKRA_LOG_DIR"] = str(tmp / "logs")
    from app.config import config_hash, get_config, model_label
    from app.services import workflow

    workflow.ensure_ready()
    cases = [json.loads(l) for l in (ROOT / "evals" / "golden.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    results = []
    for case in cases:
        r = workflow.ask(case["question"], "supervisor", "eval.runner")
        fails = check(case, r)
        results.append({"id": case["id"], "type": case["type"], "question": case["question"], "passed": not fails,
                        "failures": fails, "status": r.status, "categories": r.route.categories if r.route else [],
                        "primary": r.route.primary if r.route else None,
                        "cited": [c.chunk_id for c in r.citations], "latency_ms": r.latency_ms})

    def rate(pred):
        sel = [x for x in results if pred(x)]
        return round(100 * sum(x["passed"] for x in sel) / len(sel), 1) if sel else None

    routed = [(c, x) for c, x in zip(cases, results) if "expect_primary" in c]
    safety_cases = [(c, x) for c, x in zip(cases, results) if c.get("expect_safety_citation")]
    lat = [x["latency_ms"] for x in results]
    summary = {
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": model_label(), "llm_provider": get_config()["llm"]["provider"], "config_hash": config_hash(),
        "total": len(results), "passed": sum(x["passed"] for x in results),
        "pass_rate": rate(lambda x: True),
        "by_type": {t: rate(lambda x, t=t: x["type"] == t) for t in sorted({x["type"] for x in results})},
        "routing_accuracy": round(100 * sum(x["primary"] == c["expect_primary"] for c, x in routed) / len(routed), 1),
        "citation_hit_rate": round(100 * sum(c["expect_cited_doc"] in " ".join(x["cited"]) for c, x in zip(cases, results)
                                             if "expect_cited_doc" in c) / sum("expect_cited_doc" in c for c in cases), 1),
        "abstain_correctness": rate(lambda x: x["type"] == "negative"),
        "safety_inclusion_recall": round(100 * sum(any("SOP-" in cid for cid in x["cited"]) for _, x in safety_cases) / len(safety_cases), 1),
        "draft_leak_count": sum(any(cid.split("#")[0].endswith("-v2") for cid in x["cited"]) for x in results),
        "p95_latency_ms": round(statistics.quantiles(lat, n=20)[-1], 2) if len(lat) > 1 else lat[0],
        "note": ("mock provider: pass rate validates pipeline wiring (routing, retrieval, guardrails, grounding), "
                 "NOT live LLM answer quality - live LLM eval deferred") if get_config()["llm"]["provider"] == "mock" else "",
    }
    out = {"summary": summary, "config_snapshot": get_config(), "cases": results}
    res_dir = ROOT / "evals" / "results"
    res_dir.mkdir(parents=True, exist_ok=True)
    (res_dir / "latest.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    (res_dir / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    print(f"\nMIKRA eval - {summary['model']}  ({summary['passed']}/{summary['total']} passed, {summary['pass_rate']}%)")
    for k in ("routing_accuracy", "citation_hit_rate", "abstain_correctness", "safety_inclusion_recall",
              "draft_leak_count", "p95_latency_ms"):
        print(f"  {k:26s} {summary[k]}")
    print("  by type:", summary["by_type"])
    for x in results:
        if not x["passed"]:
            print(f"  FAIL {x['id']} {x['question'][:60]!r}: {'; '.join(x['failures'])}")
    if summary["note"]:
        print("  NOTE:", summary["note"])
    return 0 if summary["passed"] == summary["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
