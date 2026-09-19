# Starts the backend, and the frontend if it exists.
# Usage:  .\run.ps1
$ErrorActionPreference = "Stop"
$env:Path += ";C:\Program Files\nodejs"

$root = $PSScriptRoot
$py   = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $py)) { Write-Error "venv not found at $py"; exit 1 }

Write-Host "Starting backend on http://localhost:8000 ..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
  "-NoExit","-Command",
  "cd '$root'; & '$py' -m uvicorn backend.app.main:app --reload --port 8000"
)

Start-Sleep -Seconds 2

if (Test-Path (Join-Path $root "frontend\package.json")) {
  Write-Host "Starting frontend on http://localhost:5173 ..." -ForegroundColor Cyan
  Start-Process powershell -ArgumentList @(
    "-NoExit","-Command",
    "cd '$root\frontend'; npm run dev"
  )
}

Write-Host ""
Write-Host "Backend docs:  http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Health check:  http://localhost:8000/api/health" -ForegroundColor Green
