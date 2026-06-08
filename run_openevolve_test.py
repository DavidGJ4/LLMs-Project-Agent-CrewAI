"""
run_openevolve_test.py — OpenEvolve integration smoke / integration test.

Uses dummy_dataset + dummy_tasks (same paths as openevolve_evaluator.py).
Does not replace run_test.py (official test-day runner).

Usage:
  uv run python run_openevolve_test.py --mock          # zero-cost structural check
  uv run python run_openevolve_test.py --tasks 1       # lab smoke test (1 task)
  uv run python run_openevolve_test.py --tasks 5       # fuller integration test
"""
import argparse
import json
import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="OpenEvolve integration test (dummy_dataset)")
    p.add_argument("--mock", action="store_true", help="Mock LLM (no API tokens)")
    p.add_argument("--tasks", type=int, default=None, help="Number of tasks (default: all)")
    p.add_argument("--threads", type=int, default=2, help="Thread pool workers")
    return p.parse_args()


def install_mock_llm() -> None:
    from unittest.mock import patch
    import litellm

    def fake_completion(*args, **kwargs):
        return litellm.ModelResponse(
            id="mock-id",
            choices=[
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": (
                            '{"stars": 4.0, "review": "[Mocked LLM] Solid spot, would visit again."}'
                        ),
                    },
                    "finish_reason": "stop",
                }
            ],
            model="mock",
            usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        )

    patcher = patch("litellm.completion", side_effect=fake_completion)
    patcher.start()
    os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY") or "sk-mock-key"
    os.environ.pop("CREWAI_KNOWLEDGE_FILE", None)
    os.environ.pop("CREWAI_KNOWLEDGE_JSON", None)
    os.environ.pop("CREWAI_ENABLE_KNOWLEDGE", None)
    print("Mode: Mock LLM (no tokens consumed)")


def main() -> int:
    args = parse_args()

    if args.mock:
        install_mock_llm()
    else:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        api_base = os.environ.get("OPENAI_API_BASE", "")
        print("Mode: Real LLM")
        print(f"API Key: {'set' if api_key else 'MISSING'}")
        print(f"Base URL: {api_base or 'MISSING'}")

    from websocietysimulator import Simulator
    from crewai_simulation_agent import CrewAISimulationAgent

    logging.basicConfig(level=logging.INFO)

    print("\n" + "=" * 60)
    print("OpenEvolve integration test (dummy_dataset)")
    print("=" * 60)

    try:
        print(">>> Loading dummy_dataset...")
        simulator = Simulator(data_dir="dummy_dataset", device="cpu", cache=True)
        simulator.set_task_and_groundtruth(
            task_dir="dummy_tasks",
            groundtruth_dir="dummy_groundtruth",
        )
        simulator.set_agent(CrewAISimulationAgent)

        task_desc = "all" if args.tasks is None else str(args.tasks)
        print(f"\n>>> Running inference (tasks={task_desc}, threads={args.threads})...")
        simulator.run_simulation(
            number_of_tasks=args.tasks,
            enable_threading=True,
            max_workers=args.threads,
        )

        print("\n>>> Official metrics:")
        evaluation_results = simulator.evaluate()
        print(json.dumps(evaluation_results, indent=2, ensure_ascii=False))

        metrics = (
            evaluation_results.get("metrics", {})
            if isinstance(evaluation_results, dict)
            else {}
        )
        overall = metrics.get("overall_quality", 0.0)
        print(f"\nIntegration test complete! overall_quality: {overall:.4f}")
        return 0

    except Exception as e:
        print(f"\nTest aborted: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
