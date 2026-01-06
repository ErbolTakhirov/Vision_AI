@echo off
chcp 65001 > nul
echo ===================================================
echo   VISION AI PROJECT LAUNCHER 🚀
echo ===================================================
echo.
set /p clean="Kill old Python processes? (y/n): "
if "%clean%"=="y" (
    taskkill /F /IM python.exe
    taskkill /F /IM ngrok.exe
    echo Old processes killed.
)

echo.
echo [1/3] Checking Virtual Environment...
if exist venv (
    call venv\Scripts\activate
) else (
    echo Venv not found! Please run 'python -m venv venv' first.
    pause
    exit
)

echo.
echo [2/3] Preparing Django...
echo Applying migrations...
python manage.py migrate --noinput

echo.
echo [3/3] STARTING SERVER...
echo.
echo ⚠️  ВАЖНО:
echo 1. Откройте новый терминал и запустите 'ngrok http 8000'
echo 2. Скопируйте HTTPS ссылку (например https://xxxx.ngrok-free.app)
echo 3. Вставьте эту ссылку в .env (WEBAPP_URL) и в коде Mobile App если требуется.
echo.
echo Server running at http://127.0.0.1:8000
echo Ctrl+C to stop.
echo.

python manage.py runserver 0.0.0.0:8000
