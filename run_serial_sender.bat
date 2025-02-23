@echo off
setlocal

:: Check if Python is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python and add it to PATH.
    pause
    exit /b
)

:: Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate virtual environment
call venv\Scripts\activate

:: Install required Python packages
echo Installing dependencies...
pip install --upgrade pip
pip install pyserial PyQt6

:: Run the Python script
echo Launching Serial Command Sender...
start /b python serial_command_sender.py

:: Deactivate virtual environment after script execution (not required for GUI apps)
endlocal
