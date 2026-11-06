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

:: Reproducible build: PyInstaller stamps the EXE's PE header with the current
:: build time unless SOURCE_DATE_EPOCH is set, and the module graph traversal
:: (which orders base_library.zip's entries) is hash-seed dependent, so pin
:: PYTHONHASHSEED. Both values must stay in sync with the winget manifest's
:: InstallerSha256, which is generated from a build with these settings.
set "SOURCE_DATE_EPOCH=1700000000"
set "PYTHONHASHSEED=42"

echo [1/3] Compiling Qt UI and resources...
uv run python scripts\compileUI.py
if errorlevel 1 exit /b 1

echo [2/3] Freezing the application with PyInstaller...
uv run python scripts\normalize-mtimes.py .venv src
if errorlevel 1 exit /b 1
uv run pyinstaller --clean --noconfirm mollana.spec
if errorlevel 1 exit /b 1

echo [3/3] Building the Windows installer with Inno Setup...
uv run python scripts\normalize-mtimes.py dist build installer LICENSE.txt
if errorlevel 1 exit /b 1
"%ISCC%" "installer\mollana.iss"
if errorlevel 1 exit /b 1

echo.
echo Done. The installer is in dist\.
endlocal
