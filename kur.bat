@echo off
rem Video Indirici kurulumu (Windows)
cd /d %~dp0

python --version >nul 2>nul || (echo HATA: Python 3 kurulu degil. https://python.org adresinden kurun. & pause & exit /b 1)
where ffmpeg >nul 2>nul || echo UYARI: ffmpeg bulunamadi. Kurmak icin: winget install Gyan.FFmpeg

python -m venv .venv
.venv\Scripts\pip install -q -U yt-dlp[default,curl-cffi]

echo.
echo Kurulum tamam.
echo 1) Sunucuyu baslat: baslat.bat
echo 2) Chrome ^> chrome://extensions ^> Gelistirici modu ^> Paketlenmemis oge yukle ^> 'eklenti' klasoru
pause
