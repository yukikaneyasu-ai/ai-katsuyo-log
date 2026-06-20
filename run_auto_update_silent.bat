@echo off
cd /d %~dp0
call venv\Scripts\activate.bat
python auto_update.py >> auto_update.log 2>&1
