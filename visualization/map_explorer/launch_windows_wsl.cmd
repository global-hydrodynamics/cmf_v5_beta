@echo off
setlocal DisableDelayedExpansion
powershell.exe -NoProfile -STA -ExecutionPolicy Bypass -File "%~dp0launch_windows_wsl.ps1" %*
set "CMF_EXIT=%ERRORLEVEL%"
if not "%CMF_EXIT%"=="0" pause
exit /b %CMF_EXIT%
