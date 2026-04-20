@echo off
echo.
echo  PaisaCoach -- AI Financial Copilot
echo  ====================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.9+ from python.org
    pause
    exit /b 1
)

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt -q

if not exist ".env" (
    copy .env.example .env
    echo Created .env file. Edit it to add your ANTHROPIC_API_KEY.
)

echo Running migrations...
python manage.py migrate --run-syncdb -v 0

echo.
echo  Setup complete!
echo  Open: http://127.0.0.1:8000
echo  Click "Try with Demo Data" to get started instantly
echo.

python manage.py runserver
pause
