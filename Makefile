# Makefile — OpenEvolve integration (AgentSociety lab)
# On Windows without `make`, run the equivalent `uv run` commands shown in each target.

.DEFAULT_GOAL := help

ITERS ?= 10
TASKS ?= 5
OUTPUT ?= config/openevolve_output

UV := uv run --env-file .env

.PHONY: install
install: ## Sync dependencies (uv sync)
	uv sync

.PHONY: test-mock
test-mock: ## Mock integration test (dummy_dataset, zero cost)
	$(UV) python run_openevolve_test.py --mock

.PHONY: test
test: ## Real LLM integration test (all dummy tasks)
	$(UV) python run_openevolve_test.py

.PHONY: smoke
smoke: ## Lab smoke test (1 task on dummy_dataset)
	$(UV) python run_openevolve_test.py --tasks 1

.PHONY: evolve
evolve: ## Start OpenEvolve evolution (ITERS=N TASKS=N)
	set OPENEVOLVE_NUM_TASKS=$(TASKS) && $(UV) python -m openevolve.cli config/agents_evolving.yaml openevolve_evaluator.py --config config/openevolve_config.yaml --output $(OUTPUT) --iterations $(ITERS)

.PHONY: evolve-resume
evolve-resume: ## Resume from CHECKPOINT=path
	@if "$(CHECKPOINT)"=="" (echo ERROR: set CHECKPOINT=... && exit /b 1)
	set OPENEVOLVE_NUM_TASKS=$(TASKS) && $(UV) python -m openevolve.cli config/agents_evolving.yaml openevolve_evaluator.py --config config/openevolve_config.yaml --output $(OUTPUT) --checkpoint $(CHECKPOINT) --iterations $(ITERS)

.PHONY: evolve-test
evolve-test: ## Test evaluator only (no evolution loop)
	$(UV) python openevolve_evaluator.py

.PHONY: evolve-lab
evolve-lab: ## Lab deliverable: 50 iter x 1 task (rubric)
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_evolve_lab.ps1 -Iters 50 -Tasks 1

.PHONY: visualize
visualize: ## OpenEvolve visualizer at http://127.0.0.1:8080
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_visualizer.ps1

.PHONY: submit-copy
submit-copy: ## Copy best_program.yaml into lab_submission/
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/copy_lab_submission.ps1

.PHONY: evolve-report
evolve-report: ## Regenerate evolution_report.md + evolution_summary.json
	$(UV) python scripts/summarize_evolution.py

.PHONY: holdout
holdout: ## Hold-out generalization eval (5 tasks)
	$(UV) python scripts/run_holdout_eval.py --tasks 5

.PHONY: ablation
ablation: ## Ablation study (seed vs evolved vs adapter toggles)
	$(UV) python scripts/run_ablation_study.py

.PHONY: lab-package
lab-package: submit-copy holdout ablation ## Full lab_submission bundle

.PHONY: help
help: ## List targets
	@echo install test-mock test smoke evolve evolve-lab evolve-test evolve-resume visualize submit-copy
