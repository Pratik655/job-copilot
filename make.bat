@echo off
setlocal

set PORT=8765
set HOST=127.0.0.1

if exist ".venv\Scripts\python.exe" (
    set PYTHON=.venv\Scripts\python.exe
) else (
    set PYTHON=python
)

if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="install" goto install
if "%1"=="findjob" goto findjob
if "%1"=="stats" goto stats
if "%1"=="serve" goto serve
if "%1"=="run" goto run
if "%1"=="ingest" goto ingest
if "%1"=="score" goto score
if "%1"=="rescore" goto rescore

echo Unknown target: %1
goto help

:help
echo make findjob  — ingest watchlist + inbox, score new jobs, open the review UI
echo make serve    — review UI only (http://%HOST%:%PORT%)
echo make stats    — display pipeline metrics and domain breakdown
echo make run      — ingest + score, then exit
echo make ingest   — pull jobs, do not score
echo make score    — score status=new jobs only
echo make rescore  — re-score all jobs in database
goto :eof

:install
if not exist ".venv" (
    python -m venv .venv
)
%PYTHON% -m pip install -q -e .
goto :eof

:findjob
%PYTHON% -m jobcopilot run
echo Opening review UI at http://%HOST%:%PORT%
%PYTHON% -m jobcopilot serve --host %HOST% --port %PORT%
goto :eof

:stats
%PYTHON% -m jobcopilot stats
goto :eof

:serve
%PYTHON% -m jobcopilot serve --host %HOST% --port %PORT%
goto :eof

:run
%PYTHON% -m jobcopilot run
goto :eof

:ingest
%PYTHON% -m jobcopilot ingest
goto :eof

:score
%PYTHON% -m jobcopilot score
goto :eof

:rescore
%PYTHON% -m jobcopilot rescore
goto :eof

