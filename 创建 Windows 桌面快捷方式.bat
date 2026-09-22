@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$root=(Resolve-Path '.').Path; $desktop=[Environment]::GetFolderPath('Desktop'); $shell=New-Object -ComObject WScript.Shell; $link=$shell.CreateShortcut((Join-Path $desktop 'APIson.lnk')); $link.TargetPath=(Join-Path $root 'start_gui.bat'); $link.WorkingDirectory=$root; $link.IconLocation=(Join-Path $root 'assets\icon-mk.ico') + ',0'; $link.Description='APIson 多模型 Agent 协作工具'; $link.Save()"
if errorlevel 1 (
    echo [APIson] 创建快捷方式失败。
) else (
    echo [APIson] 桌面快捷方式已创建。
)
pause
endlocal
