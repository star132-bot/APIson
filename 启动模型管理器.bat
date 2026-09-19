@echo off
chcp 65001 >nul
title Agent Model Connect
cd /d "%~dp0"
start pythonw gui.py
exit
