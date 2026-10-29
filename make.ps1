param(
    [Parameter(Position=0)]
    [string]$Target = "help",
    [string]$HostName = "127.0.0.1",
    [int]$Port = 8765
)

$Python = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }

switch ($Target.ToLower()) {
    "help" {
        Write-Host "make findjob  - ingest watchlist + inbox, score new jobs, open review UI"
        Write-Host "make serve    - review UI only (http://${HostName}:${Port})"
        Write-Host "make stats    - display pipeline metrics and domain breakdown"
        Write-Host "make run      - ingest + score, then exit"
        Write-Host "make ingest   - pull jobs, do not score"
        Write-Host "make score    - score status=new jobs only"
        Write-Host "make rescore  - re-score all jobs in database"
    }
    "install" {
        if (-not (Test-Path ".venv")) { python -m venv .venv }
        & $Python -m pip install -q -e .
    }
    "findjob" {
        & $Python -m jobcopilot run
        Write-Host "Opening review UI at http://${HostName}:${Port}"
        & $Python -m jobcopilot serve --host $HostName --port $Port
    }
    "serve" {
        & $Python -m jobcopilot serve --host $HostName --port $Port
    }
    "stats" {
        & $Python -m jobcopilot stats
    }
    "run" {
        & $Python -m jobcopilot run
    }
    "ingest" {
        & $Python -m jobcopilot ingest
    }
    "score" {
        & $Python -m jobcopilot score
    }
    "rescore" {
        & $Python -m jobcopilot rescore
    }
    default {
        Write-Host "Unknown target: $Target"
        Write-Host "Run '.\make.ps1 help' for options."
    }
}
