# Copy best evolved YAML + analysis artifacts into lab_submission/
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$bestYaml = "config/openevolve_output/best/best_program.yaml"
$bestInfo = "config/openevolve_output/best/best_program_info.json"
$dest = "lab_submission"

if (-not (Test-Path $bestYaml)) {
    Write-Host "best/ missing - recovering from checkpoint_30..."
    uv run python scripts/finalize_openevolve_output.py
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

New-Item -ItemType Directory -Force -Path $dest | Out-Null
Copy-Item $bestYaml (Join-Path $dest "best_program.yaml") -Force
if (Test-Path $bestInfo) {
    Copy-Item $bestInfo (Join-Path $dest "best_program_info.json") -Force
}

# Never deploy invalid NVIDIA model id (minimax-m2 -> 404)
uv run python scripts/fix_agents_model_id.py `
    (Join-Path $dest "best_program.yaml") `
    "config/agents.yaml"

if (Test-Path "config/openevolve_output/checkpoints") {
    Write-Host "Regenerating evolution report..."
    uv run python scripts/summarize_evolution.py
}

Write-Host "Copied to $dest/"
Get-ChildItem $dest
if (Test-Path $bestInfo) {
    Write-Host ""
    Get-Content $bestInfo
}
