@echo off
setlocal
cd /d "%~dp0\.."

where uv >nul 2>nul
if errorlevel 1 (
    echo [error] uv was not found on PATH. Install it from https://docs.astral.sh/uv/
    exit /b 1
)

set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
    echo [error] Inno Setup 6 was not found. Install it from https://jrsoftware.org/isdl.php
    exit /b 1
)

echo [1/3] Compiling Qt UI and resources...
uv run python scripts\compileUI.py
if errorlevel 1 exit /b 1

echo [2/3] Freezing the application with PyInstaller...
uv run pyinstaller --clean --noconfirm mollana.spec
if errorlevel 1 exit /b 1

echo [3/3] Building the Windows installer with Inno Setup...
"%ISCC%" "installer\mollana.iss"
if errorlevel 1 exit /b 1

echo.
echo Done. The installer is in dist\.
endlocal
