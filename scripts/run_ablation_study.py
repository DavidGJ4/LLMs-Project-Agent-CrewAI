"""
Ablation study: seed prompts vs evolved prompts (+ optional adapter toggles).

Uses --mock by default for fast CI-style verification; pass no --mock for real LLM.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

if sys.prefix == sys.base_prefix:
    print("[ERROR] Run with: uv run python scripts/run_ablation_study.py", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from crewai_simulation_agent import CrewAISimulationAgent
from websocietysimulator import Simulator


def _evaluate_variant(
    simulator: Simulator,
    *,
    agents_yaml: Path,
    disable_calibration: bool = False,
    disable_repair: bool = False,
    num_tasks: int = 1,
) -> dict:
    os.environ["OPENEVOLVE_AGENTS_YAML"] = str(agents_yaml.resolve())
    os.environ["CREWAI_DISABLE_CALIBRATION"] = "1" if disable_calibration else "0"
    os.environ["CREWAI_DISABLE_REPAIR"] = "1" if disable_repair else "0"

    simulator.simulation_outputs = []
    simulator.run_simulation(
        number_of_tasks=num_tasks,
        enable_threading=False,
        max_workers=1,
    )
    eval_results = simulator.evaluate()
    metrics = eval_results.get("metrics", {}) if isinstance(eval_results, dict) else {}
    return {k: float(v) for k, v in metrics.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description="Ablation study for AgentSociety crew")
    parser.add_argument("--tasks", type=int, default=1)
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--out", default=str(ROOT / "lab_submission" / "ablation_results.json"))
    args = parser.parse_args()

    if args.mock:
        from unittest.mock import patch
        import litellm

        def fake_completion(*a, **kw):
            return litellm.ModelResponse(
                choices=[litellm.Choices(
                    message=litellm.Message(
                        content='{"stars": 4.0, "review": "[Mock ablation] Good food and service."}',
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

    seed = ROOT / "config" / "agents_evolving.yaml"
    evolved = ROOT / "config" / "agents.yaml"
    if (ROOT / "lab_submission" / "best_program.yaml").exists():
        evolved = ROOT / "lab_submission" / "best_program.yaml"

    logging_import = __import__("logging")
    logging_import.basicConfig(level=logging_import.WARNING)

    simulator = Simulator(data_dir="dummy_dataset", device="cpu", cache=True)
    simulator.set_task_and_groundtruth(task_dir="dummy_tasks", groundtruth_dir="dummy_groundtruth")
    simulator.set_agent(CrewAISimulationAgent)

    variants = [
        ("seed_prompts", seed, False, False),
        ("evolved_prompts", evolved, False, False),
        ("evolved_no_calibration", evolved, True, False),
        ("evolved_no_repair", evolved, False, True),
    ]

    results = []
    for name, yaml_path, no_cal, no_repair in variants:
        if not yaml_path.exists():
            continue
        metrics = _evaluate_variant(
            simulator,
            agents_yaml=yaml_path,
            disable_calibration=no_cal,
            disable_repair=no_repair,
            num_tasks=args.tasks,
        )
        results.append(
            {
                "variant": name,
                "agents_yaml": str(yaml_path),
                "disable_calibration": no_cal,
                "disable_repair": no_repair,
                "metrics": metrics,
            }
        )
        print(f"{name}: overall_quality={metrics.get('overall_quality', 0):.4f}")

    report = {
        "mode": "mock" if args.mock else "real_llm",
        "tasks": args.tasks,
        "interpretation": (
            "Compare seed vs evolved to isolate OpenEvolve contribution; "
            "no_calibration / no_repair isolate adapter engineering."
        ),
        "variants": results,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
