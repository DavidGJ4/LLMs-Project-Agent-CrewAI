# Final Project Report — AgentSociety CrewAI + OpenEvolve

**Author:** DavidGJ4  
**Repository:** [LLMs-Project-Agent-CrewAI](https://github.com/DavidGJ4/LLMs-Project-Agent-CrewAI)

## 1. Problem formulation

Simulate a Yelp user's **star rating** and **review text** for a held user–item pair using a multi-agent CrewAI pipeline, evaluated by the official AgentSociety `SimulationEvaluator` (`preference_estimation` + `review_generation` → `overall_quality`).

**Research question:** Can OpenEvolve improve agent *persona instructions* when task protocol and data injection are held fixed?

## 2. Architecture (three layers)

| Layer | Role | Evolved? |
|-------|------|----------|
| OpenEvolve | Mutates `config/agents_evolving.yaml` EVOLVE-BLOCK | **Yes** |
| CrewAI + adapter | Sequential 2-agent crew; pre-fetch Yelp data; calibration prior | Partially (prompts only) |
| `websocietysimulator` | InteractionTool + official metrics | No |

**Agents:** `psychological_analyst` (compatibility / rating habits) → `behavior_simulator` (JSON `{stars, review}`).

**Fixed engineering (not evolved):** `config/tasks.yaml` HEAD_A/HEAD_B protocol, `PRIOR_STAR_ESTIMATE` in `crewai_simulation_agent.py`, deterministic Yelp pre-fetch.

## 3. OpenEvolve configuration

- **Genome:** single `EVOLVE-BLOCK` (both agents' `role` / `goal` / `backstory`)
- **Mutator:** full YAML rewrite (`diff_based_evolution: false`)
- **Search:** MAP-Elites — islands=3, population=50, features `complexity` + `diversity`
- **Fitness:** `combined_score = overall_quality` (+ soft penalties for YAML errors, timeouts, crew fallbacks)
- **Rubric run:** 50 iterations × 1 task (`make evolve-lab`)

See `docs/evolution_report.md` for trajectory, lineage, and emergent strategies.

## 4. Results

| Metric | Value | Notes |
|--------|-------|-------|
| Best `combined_score` | **~0.967** | `lab_submission/best_program_info.json` |
| Smoke test (post model fix) | **~0.95** | `minimaxai/minimax-m2.7` on NVIDIA NIM |
| Evolution plateau | Early (iter 1–2) | Strong fixed scaffold; evolution refines wording |

**Generalization:** Run `uv run python scripts/run_holdout_eval.py --tasks 5` and cite `lab_submission/holdout_results.json`.

**Ablation:** Run `uv run python scripts/run_ablation_study.py` — compares seed vs evolved prompts and adapter toggles (`CREWAI_DISABLE_CALIBRATION`, `CREWAI_DISABLE_REPAIR`).

## 5. Novelty & creativity (rubric alignment)

### What is standard
- Evolving agent backstories via OpenEvolve (course lab template)
- Sequential CrewAI process

### What is distinctive in *this* project
1. **Separation of concerns:** evolution targets persona YAML only; task rubric + calibration are ablated separately — supports scientific claims about *what* improved fitness.
2. **Multi-metric evaluator + soft failure scores** (`openevolve_evaluator.py`) — avoids fitness cliffs and logs `preference_estimation` / `review_generation` / `fallback_count`.
3. **Automated evolution autopsy** (`scripts/summarize_evolution.py`) — lineage, hall-of-shame, emergent strategy extraction for the report.
4. **Hold-out task evaluation** — addresses single-task overfitting objection.
5. **Emergent prompt strategies** (from evolution): explicit star-adjustment heuristics for critical users; statistical citation requirements in analyst goals.

## 6. Evolution analysis deliverables

| Artifact | Path |
|----------|------|
| Evolved prompts | `lab_submission/best_program.yaml` |
| Score metadata | `lab_submission/best_program_info.json` |
| Machine-readable analytics | `lab_submission/evolution_summary.json` |
| Narrative report | `lab_submission/evolution_report.md` |
| Hold-out metrics | `lab_submission/holdout_results.json` |
| Ablation table | `lab_submission/ablation_results.json` |

## 7. Reproduce

```bash
uv sync
cp .env.example .env          # OPENAI_API_KEY + OPENAI_API_BASE (NVIDIA NIM)
make smoke
make evolve-lab               # 50 × 1 task
.\scripts\copy_lab_submission.ps1
uv run python scripts/run_holdout_eval.py --tasks 5
uv run python scripts/run_ablation_study.py
```

**Dataset:** `dummy_tasks/` + `dummy_groundtruth/` in repo; `dummy_dataset/` JSON must be present locally (LMDB cache rebuilds on first run).

## 8. Limitations & future work

- Fitness on 1 task during evolution → hold-out script mitigates but multi-task evolution is future work.
- Topology / tool-selection evolution not explored (tools intentionally removed for grounding).
- Token-cost multi-objective Pareto frontier not yet in fitness (metrics hooks ready).

## 9. References

- AgentSociety Challenge / WebSocietySimulator
- OpenEvolve (MAP-Elites prompt evolution)
- Course lab integration guide (EVOLVE-BLOCK, `openevolve_evaluator.py`)
