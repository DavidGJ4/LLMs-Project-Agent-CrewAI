import os
import sys
import logging
import tempfile
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.append(project_dir)

from websocietysimulator import Simulator
from crewai_simulation_agent import CrewAISimulationAgent
from src.utils.agents_yaml_io import repair_agents_yaml_file

SIM_TIMEOUT_SEC = int(os.environ.get("OPENEVOLVE_SIM_TIMEOUT", 900))
FALLBACK_REVIEW_MARKER = "Crew execution failed; falling back"

# Soft floor scores avoid artificial fitness cliffs (MAP-Elites needs gradient signal).
_SOFT_SCORES = {
    "yaml_invalid": 0.03,
    "timeout": 0.06,
    "runtime_error": 0.04,
    "crew_fallback": 0.12,
}

_simulator: Simulator | None = None


def _get_simulator() -> Simulator:
    global _simulator
    if _simulator is None:
        logging.getLogger().setLevel(logging.WARNING)
        print("[Evaluator] Initializing Simulator with dummy_dataset (one-time)...")
        _simulator = Simulator(data_dir="dummy_dataset", device="cpu", cache=True)
        _simulator.set_task_and_groundtruth(
            task_dir="dummy_tasks",
            groundtruth_dir="dummy_groundtruth",
        )
        _simulator.set_agent(CrewAISimulationAgent)
        print("[Evaluator] Simulator ready.")
    return _simulator


def _count_crew_fallbacks(outputs: list) -> int:
    count = 0
    for row in outputs or []:
        if not isinstance(row, dict):
            continue
        review = str((row.get("output") or {}).get("review", ""))
        if FALLBACK_REVIEW_MARKER in review:
            count += 1
    return count


def _apply_fallback_penalty(overall_quality: float, fallback_count: int, num_tasks: int) -> float:
    if fallback_count <= 0 or num_tasks <= 0:
        return overall_quality
    ratio = fallback_count / num_tasks
    penalty = min(0.35, 0.35 * ratio)
    return max(0.0, overall_quality - penalty)


def _result_metrics(
    *,
    combined_score: float,
    preference_estimation: float = 0.0,
    review_generation: float = 0.0,
    failure_type: str = "",
    fallback_count: int = 0,
    tasks_run: int = 0,
) -> dict:
    """OpenEvolve primary key is combined_score; extra keys support analysis."""
    out = {
        "combined_score": float(combined_score),
        "preference_estimation": float(preference_estimation),
        "review_generation": float(review_generation),
        "fallback_count": int(fallback_count),
        "tasks_run": int(tasks_run),
    }
    if failure_type:
        out["failure_type"] = failure_type
    return out


def evaluate(program_path: str) -> dict:
    """OpenEvolve fitness: run CrewAI simulation with mutated agents YAML."""
    simulator = _get_simulator()
    num_tasks = int(os.environ.get("OPENEVOLVE_NUM_TASKS", 5))

    try:
        try:
            repair_agents_yaml_file(program_path)
        except Exception as fix_err:
            print(f"[Evaluator] Could not sanitize YAML ({program_path}): {fix_err}")
            return _result_metrics(
                combined_score=_SOFT_SCORES["yaml_invalid"],
                failure_type="yaml_invalid",
                tasks_run=0,
            )

        os.environ["OPENEVOLVE_AGENTS_YAML"] = program_path
        print(
            f"\n[Evaluator] Running simulation: {program_path} "
            f"(tasks={num_tasks}, timeout={SIM_TIMEOUT_SEC}s)"
        )

        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    simulator.run_simulation,
                    number_of_tasks=num_tasks,
                    enable_threading=True,
                    max_workers=2,
                )
                future.result(timeout=SIM_TIMEOUT_SEC)
        except FuturesTimeout:
            print(f"[Evaluator] Simulation exceeded {SIM_TIMEOUT_SEC}s — soft penalty score")
            return _result_metrics(
                combined_score=_SOFT_SCORES["timeout"],
                failure_type="timeout",
                tasks_run=num_tasks,
            )

        outputs = [r for r in (simulator.simulation_outputs or []) if r is not None]
        fallback_count = _count_crew_fallbacks(outputs)

        print("[Evaluator] Calculating official metrics...")
        eval_results = simulator.evaluate()
        metrics = eval_results.get("metrics", {}) if isinstance(eval_results, dict) else {}
        overall_quality = float(metrics.get("overall_quality", 0.0))
        pref_estimation = float(metrics.get("preference_estimation", 0.0))
        review_generation = float(metrics.get("review_generation", 0.0))

        if fallback_count > 0:
            overall_quality = _apply_fallback_penalty(overall_quality, fallback_count, num_tasks)
            print(
                f"[Evaluator] Applied fallback penalty: {fallback_count}/{num_tasks} tasks "
                f"-> combined_score={overall_quality:.4f}"
            )

        print(
            f"[Evaluator] preference_estimation={pref_estimation:.4f}, "
            f"review_generation={review_generation:.4f}, "
            f"overall_quality={overall_quality:.4f} -> combined_score={overall_quality:.4f}"
        )
        return _result_metrics(
            combined_score=overall_quality,
            preference_estimation=pref_estimation,
            review_generation=review_generation,
            fallback_count=fallback_count,
            tasks_run=num_tasks,
        )

    except Exception as e:
        print(f"[Evaluator] Error during evaluation: {e}")
        import traceback

        traceback.print_exc()
        return _result_metrics(
            combined_score=_SOFT_SCORES["runtime_error"],
            failure_type="runtime_error",
            tasks_run=num_tasks,
        )


if __name__ == "__main__":
    yaml_path = os.path.join(project_dir, "config", "agents_evolving.yaml")
    if not os.path.exists(yaml_path):
        print(f"Missing {yaml_path}")
        sys.exit(1)

    with open(yaml_path, encoding="utf-8") as f:
        content = f.read()
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    try:
        fitness = evaluate(tmp_path)
        print(f"Test execution completed with fitness: {fitness}")
    finally:
        os.remove(tmp_path)
