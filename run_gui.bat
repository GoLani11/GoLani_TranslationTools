@echo off
chcp 65001 > nul
cd /d "%~dp0"
python translation_sync_gui.py
pause