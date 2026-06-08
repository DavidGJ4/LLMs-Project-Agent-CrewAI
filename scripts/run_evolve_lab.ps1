# Lab Step 5: evolve 30 iterations x 1 task (PowerShell; no make required)
param(
    [int]$Iters = 30,
    [int]$Tasks = 1,
    [string]$Output = "config/openevolve_output"
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not (Test-Path ".env")) {
    Write-Error "Missing .env - copy .env.example and set OPENAI_API_KEY / OPENAI_API_BASE"
}

$env:OPENEVOLVE_NUM_TASKS = "$Tasks"
$env:PYTHONUTF8 = "1"
Write-Host "Starting OpenEvolve: ITERS=$Iters TASKS=$Tasks OUTPUT=$Output"
Write-Host "Expect ~15-45+ minutes depending on API rate limits."

uv run --env-file .env python -m openevolve.cli `
    config/agents_evolving.yaml `
    openevolve_evaluator.py `
    --config config/openevolve_config.yaml `
    --output $Output `
    --iterations $Iters

if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "Done. Next:"
Write-Host '  1. .\scripts\run_visualizer.ps1'
Write-Host '  2. .\scripts\copy_lab_submission.ps1'
