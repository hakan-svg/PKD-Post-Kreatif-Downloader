#!/bin/zsh
# Video İndirici sunucusunu başlatır. Pencereyi kapatma; indirmeler bu süreçte çalışır.
cd "$(dirname "$0")"
exec ./.venv/bin/python sunucu.py
