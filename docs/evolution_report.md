# OpenEvolve Evolution Report

Generated: 2026-06-09T02:39:48.046183+00:00

## Executive summary

This project uses OpenEvolve to mutate the **EVOLVE-BLOCK** in `config/agents_evolving.yaml` (two pure-reasoning agents: `psychological_analyst` → `behavior_simulator`). Fitness is the official AgentSociety **`overall_quality`** metric (star accuracy + review fidelity), evaluated via `openevolve_evaluator.py`.

| Metric | Value |
|--------|-------|
| **Best combined_score** | **0.9668** |
| **Iteration found** | 15 |
| **Programs evaluated** | 234 |
| **MAP-Elites islands** | 3 |

> **Key insight:** Performance is high early because **fixed** engineering (`config/tasks.yaml` HEAD_A/HEAD_B protocol, Yelp pre-fetch, `PRIOR_STAR_ESTIMATE` calibration in `crewai_simulation_agent.py`) constrains the search space. OpenEvolve **refines** agent persona instructions inside that scaffold.

## Fitness trajectory (best score per iteration)

| Iteration | Best combined_score |
|-----------|---------------------|
| 0 | 0.9668 |
| 1 | 0.9609 |
| 2 | 0.9412 |
| 3 | 0.9498 |
| 4 | 0.9363 |
| 5 | 0.9438 |
| 6 | 0.9453 |
| 7 | 0.9618 |
| 8 | 0.9419 |
| 9 | 0.9429 |
| 10 | 0.9532 |
| 11 | 0.9578 |
| 12 | 0.9404 |
| 13 | 0.9436 |
| 14 | 0.9440 |
| … | (16 more iterations) |

**Convergence note:** High fitness often appears by iteration 1–2 because the fixed task protocol and adapter calibration provide a strong scaffold; evolution refines persona wording.

## Lineage (best program → ancestors)

- iter 15 gen 2 score 0.9668 id `9f6c8489…`
- iter 3 gen 1 score 0.9498 id `41ff0200…`
- iter 0 gen 0 score 0.9537 id `bb8cac81…`

## Emergent strategies (prompt diffs vs seed)

- Evolution lengthened analyst goals with explicit statistical citations.
- Simulator goals added numeric star adjustment tied to user rating habits.

## Evolutionary anti-patterns (failed mutations)

- Mutating llm model id to minimax-m2 (invalid on NVIDIA NIM) causes 404 crew failures.
- Broken YAML fences or inline JSON in goal fields — mitigated by repair_agents_yaml_file.
- Relying on crew fallback reviews yields ~0.72 overall_quality despite OK star priors.

## Lowest-scoring candidates (hall of shame sample)

- score 0.3892 @ iter 11 (parent 7552650e…)
- score 0.3892 @ iter 5 (parent 0efa7e89…)
- score 0.3892 @ iter 12 (parent 41ff0200…)
- score 0.3892 @ iter 11 (parent 7552650e…)
- score 0.3892 @ iter 5 (parent 0efa7e89…)

## What we did *not* evolve (scope boundary)

- Crew topology (`Process.sequential` in `simulation_crew.py`)
- Task rubric (`config/tasks.yaml` — HEAD_A_TARGET_STARS protocol)
- Adapter calibration / repair pass (`crewai_simulation_agent.py`)

This separation is intentional: evolution optimizes **persona and reasoning instructions**, while reproducible engineering handles **data grounding and output contract**.

## Reproduce

```bash
uv sync
cp .env.example .env   # add NVIDIA key
make smoke
make evolve-lab        # 50 iterations × 1 task
uv run python scripts/summarize_evolution.py
uv run python scripts/run_holdout_eval.py --tasks 5
uv run python scripts/run_ablation_study.py --mock
```

## Files for reviewers

- `lab_submission/best_program.yaml` — evolved prompts
- `lab_submission/best_program_info.json` — score metadata
- `lab_submission/evolution_summary.json` — machine-readable analytics
- `lab_submission/holdout_results.json` — generalization (after running hold-out script)
