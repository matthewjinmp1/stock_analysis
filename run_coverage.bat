@echo off
cd /d %~dp0
echo ========================================
echo Running Stock Analysis Coverage Analysis
echo ========================================
echo Running Backend Coverage...
set PYTHONPATH=%PYTHONPATH%;%CD%
python -m pytest web_app/backend/tests --cov=web_app/backend --cov-report=term-missing --cov-report=html
echo.
echo Running Frontend Coverage...
pushd web_app\frontend
call npm run test:coverage
popd
echo ========================================
echo Coverage and Tests Complete.
echo Backend HTML report available in: htmlcov\index.html
echo Frontend HTML report available in: web_app/frontend/coverage/index.html
