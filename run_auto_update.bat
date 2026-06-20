@echo off
cd /d %~dp0
if not exist venv (
    echo venv が見つかりません。先に setup_auto_update.bat を実行してください。
    pause
    exit /b
)
call venv\Scripts\activate.bat
python auto_update.py
pause
