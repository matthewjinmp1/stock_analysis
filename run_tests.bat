@echo off
echo ========================================
echo Running Stock Analysis Test Suite
echo Mode: Parallel Multithreading (Verbose)
echo ========================================
echo Running Backend Tests...
python -m pytest -n auto -v
echo.
echo Running Frontend Tests...
cd web_app/frontend
call npm test -- --run
cd ../..
echo ========================================
echo All Tests Complete.
