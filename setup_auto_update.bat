@echo off
cd /d %~dp0
where python >nul 2>nul
if errorlevel 1 (
    echo Python が見つかりませんでした。
    echo https://www.python.org/ から Python をインストールしてから、もう一度実行してください。
    pause
    exit /b
)

if exist venv (
    echo 既存の venv を削除しています...
    rmdir /s /q venv
)

echo venv を作成しています...
python -m venv venv

call venv\Scripts\activate.bat
echo 必要なパッケージをインストールしています...
python -m pip install --upgrade pip >nul
pip install feedparser

echo.
echo セットアップが完了しました。
echo 次は run_auto_update.bat を実行してください。
pause
