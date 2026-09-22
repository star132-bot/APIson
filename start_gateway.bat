@echo off
setlocal
chcp 65001 >nul
title APIson Gateway
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
    py -3 bootstrap.py gateway %*
) else (
    where python >nul 2>nul
    if not errorlevel 1 (
        python bootstrap.py gateway %*
    ) else (
        echo [APIson] 未找到 Python 3。请先从 https://www.python.org/downloads/ 安装。
        pause
        exit /b 1
    )
)
if errorlevel 1 pause
endlocal
