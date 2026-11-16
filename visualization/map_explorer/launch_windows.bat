@echo off
rem Double-click in Explorer. Paths with spaces are supported; no automatic installation.
setlocal EnableExtensions DisableDelayedExpansion
set "SCRIPT_DIR=%~dp0"
if defined PYTHON goto run_python
if defined VIRTUAL_ENV if exist "%VIRTUAL_ENV%\Scripts\python.exe" set "PYTHON=%VIRTUAL_ENV%\Scripts\python.exe"
if defined PYTHON goto run_python
if exist "%SCRIPT_DIR%..\..\.venv\Scripts\python.exe" set "PYTHON=%SCRIPT_DIR%..\..\.venv\Scripts\python.exe"
if defined PYTHON goto run_python
if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" set "PYTHON=%SCRIPT_DIR%.venv\Scripts\python.exe"
if defined PYTHON goto run_python
where py >nul 2>&1
if not errorlevel 1 goto run_py
where python >nul 2>&1
if not errorlevel 1 set "PYTHON=python"
if defined PYTHON goto run_python
echo [ERROR] Python 3.10 or later is required. See README.md.
pause
exit /b 1

:run_py
set "PYTHONDONTWRITEBYTECODE=1"
set "BOKEH_RESOURCES=server"
set "MPLBACKEND=Agg"
if not defined MPLCONFIGDIR set "MPLCONFIGDIR=%SCRIPT_DIR%output\.matplotlib"
py -3 "%SCRIPT_DIR%launch_desktop.py" %*
goto finished

:run_python
set "PYTHONDONTWRITEBYTECODE=1"
set "BOKEH_RESOURCES=server"
set "MPLBACKEND=Agg"
if not defined MPLCONFIGDIR set "MPLCONFIGDIR=%SCRIPT_DIR%output\.matplotlib"
"%PYTHON%" "%SCRIPT_DIR%launch_desktop.py" %*

:finished
set "LAUNCH_STATUS=%ERRORLEVEL%"
if not "%LAUNCH_STATUS%"=="0" pause
exit /b %LAUNCH_STATUS%
