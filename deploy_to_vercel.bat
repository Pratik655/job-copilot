@echo off
cd /d "%~dp0"
echo ==============================================================================
echo Job Copilot - 1-Click Vercel Production Deploy
echo ==============================================================================
echo.
echo Deploying latest code and database to Vercel production...
if defined VERCEL_TOKEN (
    call npx -y vercel --prod --yes --token %VERCEL_TOKEN%
) else (
    call npx -y vercel --prod --yes
)
echo.
echo ==============================================================================
echo Live Production URL: https://job-copilot-weld-seven.vercel.app
echo ==============================================================================
pause
