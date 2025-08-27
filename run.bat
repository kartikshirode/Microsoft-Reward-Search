@echo off
echo ================================================
echo Enhanced Bing Search Automation with Google News
echo ================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

echo Python found. Checking dependencies...

REM Install dependencies if needed
python -c "import requests, bs4, feedparser, fake_useragent, undetected_chromedriver, selenium" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Error: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo Dependencies OK. Starting enhanced application...
echo.
echo Features Available:
echo - Google News Integration
echo - Multiple Search Sources  
echo - Background/Headless Modes
echo - Gemini AI Support (optional)
echo.

REM Run the enhanced script
python micro_enhanced.py

echo.
echo Script finished. Press any key to exit...
pause >nul
