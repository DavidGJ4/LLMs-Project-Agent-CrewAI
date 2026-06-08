# OpenEvolve visualizer (http://127.0.0.1:8080) - no git required
param(
    [string]$Output = "config/openevolve_output"
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$repoRoot = Join-Path $PWD "vendor/openevolve-main"
$vizScript = Join-Path $repoRoot "scripts/visualizer.py"

function Install-OpenEvolveVisualizer {
    Write-Host "Downloading OpenEvolve visualizer (one-time, no git needed)..."
    $vendorDir = Join-Path $PWD "vendor"
    New-Item -ItemType Directory -Force -Path $vendorDir | Out-Null

    $zipPath = Join-Path $env:TEMP "openevolve-main.zip"
    $zipUrl = "https://github.com/algorithmicsuperintelligence/openevolve/archive/refs/heads/main.zip"

    Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -UseBasicParsing

    if (Test-Path $repoRoot) {
        Remove-Item -Recurse -Force $repoRoot
    }
    Expand-Archive -Path $zipPath -DestinationPath $vendorDir -Force
    Remove-Item $zipPath -Force -ErrorAction SilentlyContinue

    if (-not (Test-Path $vizScript)) {
        throw "Download failed: missing $vizScript"
    }
    Write-Host "Installed to $repoRoot"
}

if (-not (Test-Path $vizScript)) {
    Install-OpenEvolveVisualizer
}

$env:EVOLVE_OUTPUT = (Resolve-Path $Output).Path
Write-Host "Visualizer reading: $env:EVOLVE_OUTPUT"
Write-Host "Open http://127.0.0.1:8080 - pick checkpoint_30, highlight Top score, use Diff tab"
Set-Location (Join-Path $repoRoot "scripts")
uv run python visualizer.py --path $env:EVOLVE_OUTPUT
