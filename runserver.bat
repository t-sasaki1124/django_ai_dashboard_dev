@echo off
REM Django開発サーバーを起動するバッチファイル
REM 使用方法: runserver.bat

echo 仮想環境を有効化中...
call venv\Scripts\activate.bat

echo Djangoサーバーを起動中...
python manage.py runserver

pause

