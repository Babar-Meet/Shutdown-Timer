@echo off
echo Building Shutdown Timer executable...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install --upgrade pip
pip install pyinstaller
pip install -r requirements.txt

REM Build the executable
echo Building executable...
pyinstaller --onefile --noconsole --name "ShutdownTimer" app/main.py

REM Clean up
echo Cleaning up temporary files...
if exist "__pycache__" rmdir /s /q "__pycache__"
if exist "build" rmdir /s /q "build"
if exist "ShutdownTimer.spec" del ShutdownTimer.spec

REM Create distribution directory if it doesn't exist
if not exist "dist" mkdir dist

REM Move executable to dist directory
if exist "ShutdownTimer.exe" move /Y ShutdownTimer.exe dist\

REM Display success message
echo.
echo Build completed successfully!
echo Executable created at: dist\ShutdownTimer.exe
echo.
echo Press any key to exit...
pause >nul