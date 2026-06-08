# Lab submission (OpenEvolve Steps 4–5)

Upload the files in this folder to the course drop folder before **Monday 6/1 24:00**.

After evolution finishes, populate this directory:

```powershell
.\scripts\copy_lab_submission.ps1
```

Expected files:

- `best_program.yaml` — evolved agent prompts (from visualizer / `config/openevolve_output/best/`)
- `best_program_info.json` — `combined_score` and metadata

Optional screenshot: export from http://127.0.0.1:8080 showing `checkpoint_30` and top `combined_score`.

## For reviewers (GitHub)

1. Copy `.env.example` → `.env` and add your own `OPENAI_API_KEY` + `OPENAI_API_BASE` (NVIDIA NIM: `https://integrate.api.nvidia.com/v1`).
2. Use model `minimaxai/minimax-m2.7` in `config/agents.yaml` (already set in this repo).
3. Install: `uv sync`
4. Smoke test: `uv run --env-file .env python run_openevolve_test.py --tasks 1`
5. **Dataset:** `dummy_tasks/` and `dummy_groundtruth/` are included. `dummy_dataset/` JSON/LMDB is not in git (too large); use the course `dummy_dataset` or rebuild from the official AgentSociety materials.
