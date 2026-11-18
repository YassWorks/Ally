param([switch]$HF)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "uv is required: https://docs.astral.sh/uv/getting-started/installation/" -ForegroundColor Red
    exit 1
}

$target = if ($HF) { ".[hf]" } else { "." }

Write-Host "Installing Ally..." -ForegroundColor Cyan
uv tool install --force --editable --compile-bytecode $target
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
uv tool update-shell | Out-Null

Write-Host "Done. Open a new terminal and run: ally" -ForegroundColor Green
