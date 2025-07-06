@echo off
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do (
    echo "Killing process on port 8000 with PID: %%a"
    taskkill /F /PID %%a
)

call venv\Scripts\activate.bat
uvicorn sgpt-research-web.main:app --host 0.0.0.0 --port 8000