"""
Hold-out generalization: evaluate evolved agents on multiple dummy tasks.

Evolution typically uses OPENEVOLVE_NUM_TASKS=1 (first task). This script reports
per-task and aggregate official metrics to demonstrate generalization.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

if sys.prefix == sys.base_prefix:
    print("[ERROR] Run with: uv run python scripts/run_holdout_eval.py", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from crewai_simulation_agent import CrewAISimulationAgent
from websocietysimulator import Simulator

FALLBACK_MARKER = "Crew execution failed"


def _run_task(simulator: Simulator, task_index: int) -> dict:
    task = simulator.tasks[task_index]
    agent = CrewAISimulationAgent(llm=None)
    agent.set_interaction_tool(simulator.interaction_tool)
    agent.insert_task(task)
    t0 = time.time()
    try:
        output = agent.workflow()
        err = None
    except Exception as exc:
        output = {"stars": 0, "review": ""}
        err = str(exc)
    return {
        "task_index": task_index,
        "user_id": task.user_id,
        "item_id": task.item_id,
        "output": output,
        "elapsed_sec": round(time.time() - t0, 2),
        "error": err,
        "crew_fallback": FALLBACK_MARKER in str(output.get("review", "")),
    }


def _evaluate_subset(simulator: Simulator, indices: list[int]) -> dict:
    simulator.simulation_outputs = []
    rows = []
    for idx in indices:
        row = _run_task(simulator, idx)
        rows.append(row)
        simulator.simulation_outputs.append(
            {"task": simulator.tasks[idx].to_dict(), "output": row["output"]}
        )
    eval_results = simulator.evaluate()
    metrics = eval_results.get("metrics", {}) if isinstance(eval_results, dict) else {}
    return {
        "task_indices": indices,
        "metrics": metrics,
        "per_task": rows,
        "fallback_count": sum(1 for r in rows if r.get("crew_fallback")),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Hold-out evaluation for evolved agents")
    parser.add_argument(
        "--agents-yaml",
        default=str(ROOT / "config" / "agents.yaml"),
        help="Agents config to load via OPENEVOLVE_AGENTS_YAML",
    )
    parser.add_argument("--tasks", type=int, default=5, help="Number of tasks from start of dummy_tasks")
    parser.add_argument("--train-index", type=int, default=0, help="Task index used during evolution")
    parser.add_argument("--mock", action="store_true", help="Mock LLM (structure only)")
    parser.add_argument(
        "--out",
        default=str(ROOT / "lab_submission" / "holdout_results.json"),
    )
    args = parser.parse_args()

    if args.mock:
        from unittest.mock import patch
        import litellm

        def fake_completion(*a, **kw):
            return litellm.ModelResponse(
                choices=[litellm.Choices(
                    message=litellm.Message(
                        content='{"stars": 4.0, "review": "[Mock holdout] Solid spot, would return."}',
                        role="assistant",
                    ),
                    finish_reason="stop",
                )],
                model="mock",
            )

        patch("litellm.completion", side_effect=fake_completion).start()
        os.environ["OPENAI_API_KEY"] = "sk-mock-key"
    else:
        load_dotenv()
        if os.environ.get("OPENAI_API_BASE") and not os.environ.get("OPENAI_BASE_URL"):
            os.environ["OPENAI_BASE_URL"] = os.environ["OPENAI_API_BASE"]

    agents_path = Path(args.agents_yaml)
    if not agents_path.exists():
        print(f"Missing agents yaml: {agents_path}", file=sys.stderr)
        return 1

    os.environ["OPENEVOLVE_AGENTS_YAML"] = str(agents_path.resolve())

    logging.basicConfig(level=logging.WARNING)
    print(f"Agents: {agents_path}")
    print(f"Evaluating tasks 0..{args.tasks - 1} (train index={args.train_index})")

    simulator = Simulator(data_dir="dummy_dataset", device="cpu", cache=True)
    simulator.set_task_and_groundtruth(task_dir="dummy_tasks", groundtruth_dir="dummy_groundtruth")
    simulator.set_agent(CrewAISimulationAgent)

    n = min(args.tasks, len(simulator.tasks))
    all_indices = list(range(n))
    holdout_indices = [i for i in all_indices if i != args.train_index]

    train_result = _evaluate_subset(simulator, [args.train_index]) if args.train_index < n else None
    holdout_result = _evaluate_subset(simulator, holdout_indices) if holdout_indices else None
    full_result = _evaluate_subset(simulator, all_indices)

    report = {
        "agents_yaml": str(agents_path),
        "mode": "mock" if args.mock else "real_llm",
        "train_task_index": args.train_index,
        "train_metrics": (train_result or {}).get("metrics"),
        "holdout_task_indices": holdout_indices,
        "holdout_metrics": (holdout_result or {}).get("metrics"),
        "holdout_fallback_count": (holdout_result or {}).get("fallback_count", 0),
        "all_tasks_metrics": full_result.get("metrics"),
        "per_task": full_result.get("per_task"),
        "generalization_gap": None,
    }

    train_q = float((report.get("train_metrics") or {}).get("overall_quality", 0))
    hold_q = float((report.get("holdout_metrics") or {}).get("overall_quality", 0))
    if train_q and hold_q:
        report["generalization_gap"] = round(train_q - hold_q, 4)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))
    print(f"\nWrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
