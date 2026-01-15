@echo off
echo ========================================
echo AllergyInsight Development Server
echo ========================================
echo.

:: 백엔드 서버 시작
echo [1/2] Starting Backend Server (Port 9040)...
start "AllergyInsight Backend" cmd /k "cd /d C:\GIT\AllergyInsight\backend && python -m uvicorn app.api.main:app --reload --host 0.0.0.0 --port 9040"

:: 잠시 대기
timeout /t 3 /nobreak > nul

:: 프론트엔드 서버 시작
echo [2/2] Starting Frontend Server (Port 4040)...
start "AllergyInsight Frontend" cmd /k "cd /d C:\GIT\AllergyInsight\frontend && npm run dev"

echo.
echo ========================================
echo Servers started!
echo Backend:  http://localhost:9040
echo Frontend: http://localhost:4040
echo API Docs: http://localhost:9040/docs
echo ========================================
echo.
echo Press any key to open the dashboard...
pause > nul
start http://localhost:4040
