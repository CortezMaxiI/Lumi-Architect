@echo off
title Setup Dependencies - Lumi: Architect
echo Iniciando instalacion de dependencias...
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0setup_dependencies.ps1"
echo.
pause
