#!/usr/bin/env bash
# Video İndirici kurulumu (macOS / Linux)
set -e
cd "$(dirname "$0")"

command -v python3 >/dev/null || { echo "HATA: python3 kurulu değil."; exit 1; }
command -v ffmpeg  >/dev/null || echo "UYARI: ffmpeg bulunamadı — macOS: brew install ffmpeg | Linux: sudo apt install ffmpeg"

python3 -m venv .venv
./.venv/bin/pip install -q -U "yt-dlp[default,curl-cffi]"

echo
echo "Kurulum tamam."
echo "1) Sunucuyu başlat: baslat.command (Mac) veya ./.venv/bin/python sunucu.py"
echo "2) Chrome > chrome://extensions > Geliştirici modu > Paketlenmemiş öğe yükle > 'eklenti' klasörü"
