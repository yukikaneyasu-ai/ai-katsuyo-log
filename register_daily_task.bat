@echo off
cd /d %~dp0
set TASK_NAME=AI活用ログ自動更新

schtasks /create /tn "%TASK_NAME%" /tr "\"%~dp0run_auto_update_silent.bat\"" /sc daily /st 07:00 /f

if errorlevel 1 (
    echo タスクの登録に失敗しました。コマンドプロンプトを「管理者として実行」してから、もう一度お試しください。
) else (
    echo.
    echo 毎日 7:00 に自動更新するタスクを登録しました。
    echo タスクスケジューラ（taskschd.msc）で「%TASK_NAME%」を確認・時間変更できます。
    echo 実行ログは auto_update.log に追記されます。
)
pause
