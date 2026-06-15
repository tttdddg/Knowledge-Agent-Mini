@echo off
setlocal

if not exist .venv (
    echo [ERROR] Virtual environment not found.
    echo Please run: python -m venv .venv
    echo Then: .venv\Scripts\activate ^&^& pip install -r requirements.txt
    exit /b 1
)

call .venv\Scripts\activate

if not exist data (
    mkdir data
)

if not exist logs (
    mkdir logs
)

echo.
echo ============================================
echo   Knowledge Agent Mini
echo ============================================
echo.
echo   Open http://127.0.0.1:8000
echo   API docs: http://127.0.0.1:8000/docs
echo.
echo ============================================
echo.

uvicorn app.main:app --host 127.0.0.1 --port 8000
