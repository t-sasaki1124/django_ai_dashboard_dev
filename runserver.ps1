# Django開発サーバーを起動するPowerShellスクリプト
# 使用方法: .\runserver.ps1

$ErrorActionPreference = "Stop"

Write-Host "仮想環境を有効化中..." -ForegroundColor Green
& .\venv\Scripts\Activate.ps1

Write-Host "Djangoサーバーを起動中..." -ForegroundColor Green
python manage.py runserver

