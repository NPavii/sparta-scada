$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path .env)) {
    Write-Host "Creating .env from .env.example..."
    Copy-Item .env.example .env
}

Write-Host "Starting Sparta SCADA infrastructure..."
docker compose up -d

Write-Host ""
Write-Host "Running services:"
docker compose ps
