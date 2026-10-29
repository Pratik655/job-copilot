@echo off
cd /d "%~dp0"
echo ==============================================================================
echo Starting Job Copilot — Multi-Domain Career & Application Workspace
echo Model: Radox AI (gpt-5.6-luna)
echo URL:   http://127.0.0.1:8000
echo ==============================================================================
python -m uvicorn jobcopilot.web:app --host 127.0.0.1 --port 8000 --reload
pause
