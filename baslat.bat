@echo off
rem Sunucuyu baslatir. Pencereyi kapatma; indirmeler bu surecte calisir.
cd /d %~dp0
.venv\Scripts\python sunucu.py
