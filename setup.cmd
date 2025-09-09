@echo off
setlocal

echo === Setting up Ally ===

:: Step 1: Create virtual environment
echo Creating virtual environment...
python -m venv .venv || (
    echo Failed to create virtual environment
    exit /b 1
)

:: Step 2: Install requirements
echo Installing dependencies...
call .venv\Scripts\activate.bat
pip install -r requirements.txt || (
    echo Failed to install requirements
    exit /b 1
)

:: Step 3: Create bin\ally.bat
echo Creating launcher script...
set "CURR_DIR=%CD%"
if not exist bin mkdir bin

(
    echo @echo off
    echo "%CURR_DIR%\.venv\Scripts\activate.bat" ^&^& python "%CURR_DIR%\main.py" %%*
) > bin\ally.bat

:: Step 4: Add bin to PATH (user scope)
set "BIN_DIR=%CURR_DIR%\bin"
for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "USER_PATH=%%B"

echo ;%PATH%; | find /i ";%BIN_DIR%;" >nul
if errorlevel 1 (
    if not defined USER_PATH (
        reg add "HKCU\Environment" /v PATH /t REG_EXPAND_SZ /d "%BIN_DIR%" /f >nul
    ) else (
        reg add "HKCU\Environment" /v PATH /t REG_EXPAND_SZ /d "%USER_PATH%;%BIN_DIR%" /f >nul
    )
    echo Added %BIN_DIR% to PATH. Restart your terminal or log off/on.
) else (
    echo %BIN_DIR% is already in PATH.
)

echo === Setup complete! You can now run "ally" ===
pause
