@echo off
set RUNTIME_DIR=%~dp0..\scada-config\runtime\Instances\Default

echo Starting ScadaServer...
start "ScadaServer" /D "%RUNTIME_DIR%\ScadaServer" ScadaServerApp.exe

ping -n 4 127.0.0.1 >nul

echo Starting ScadaComm...
start "ScadaComm" /D "%RUNTIME_DIR%\ScadaComm" ScadaCommApp.exe
