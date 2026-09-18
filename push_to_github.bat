@echo off
title Push to GitHub - Lumi: Architect
cd /d "%~dp0"
echo =======================================================
echo Subiendo cambios a GitHub (origin/main)...
echo =======================================================
git push -u origin main
echo.
pause
