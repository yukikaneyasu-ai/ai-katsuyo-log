@echo off
cd /d %~dp0
where python >nul 2>nul
if errorlevel 1 (
    echo Python が見つかりませんでした。
    echo https://www.python.org/ から Python をインストールしてから、もう一度実行してください。
    pause
    exit /b
)
python server.py
pause
