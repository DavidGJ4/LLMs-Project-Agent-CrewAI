# Lab submission (OpenEvolve + Final Project)

Upload this folder (or link the GitHub repo) for course review.

## Required files

| File | Description |
|------|-------------|
| `best_program.yaml` | Evolved agent prompts (from OpenEvolve best) |
| `best_program_info.json` | `combined_score` and metadata |
| `evolution_report.md` | Evolution trajectory, lineage, emergent strategies |
| `evolution_summary.json` | Machine-readable evolution analytics |

## Recommended (strengthens grading)

| File | Description |
|------|-------------|
| `holdout_results.json` | Generalization on tasks 1–N (not only evolution train task) |
| `ablation_results.json` | Seed vs evolved vs adapter-off variants |
| `w14-lab.png` or visualizer screenshot | OpenEvolve checkpoint / fitness plot |

## Regenerate after evolution

```powershell
.\scripts\copy_lab_submission.ps1
uv run python scripts/run_holdout_eval.py --tasks 5
uv run python scripts/run_ablation_study.py
```

## For reviewers (GitHub)

1. Copy `.env.example` → `.env` — add NVIDIA `OPENAI_API_KEY` + `OPENAI_API_BASE=https://integrate.api.nvidia.com/v1`
2. Model id must be **`minimaxai/minimax-m2.7`** (in `config/agents.yaml`)
3. `uv sync` then `uv run --env-file .env python run_openevolve_test.py --tasks 1`
4. Full write-up: `docs/FINAL_PROJECT_REPORT.md`

**Note:** `dummy_dataset/` JSON is not in git (size); use course materials or local copy. `dummy_tasks/` and `dummy_groundtruth/` are included.
