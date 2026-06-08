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


def evaluate(program_path: str) -> dict:
    """OpenEvolve fitness function: run CrewAI simulation with mutated agents YAML."""
    simulator = _get_simulator()
    try:
        try:
            repair_agents_yaml_file(program_path)
        except Exception as fix_err:
            print(f"[Evaluator] Could not sanitize YAML ({program_path}): {fix_err}")
            return {"combined_score": 0.0}

        os.environ["OPENEVOLVE_AGENTS_YAML"] = program_path
        num_tasks = int(os.environ.get("OPENEVOLVE_NUM_TASKS", 5))
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
            print(f"[Evaluator] Simulation exceeded {SIM_TIMEOUT_SEC}s — returning fallback score")
            return {"combined_score": 0.0}

        print("[Evaluator] Calculating official metrics...")
        eval_results = simulator.evaluate()
        metrics = eval_results.get("metrics", {}) if isinstance(eval_results, dict) else {}
        overall_quality = float(metrics.get("overall_quality", 0.0))
        pref_estimation = float(metrics.get("preference_estimation", 0.0))
        review_generation = float(metrics.get("review_generation", 0.0))

        print(
            f"[Evaluator] preference_estimation={pref_estimation:.4f}, "
            f"review_generation={review_generation:.4f}, "
            f"overall_quality={overall_quality:.4f} -> combined_score={overall_quality:.4f}"
        )
        return {"combined_score": overall_quality}

    except Exception as e:
        print(f"[Evaluator] Error during evaluation: {e}")
        import traceback

        traceback.print_exc()
        return {"combined_score": 0.0}


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
