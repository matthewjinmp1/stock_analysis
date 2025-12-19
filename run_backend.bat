@echo off
echo ========================================
echo Starting Stock Analysis Backend
echo ========================================
set PYTHONPATH=%PYTHONPATH%;%CD%
python web_app/backend/app.py
echo ========================================
pause
