#!/usr/bin/env bash
# PKD — Post Kreatif Downloader, Mac'te TEK KOMUTLA kurulum.
# Terminal'e şunu yapıştırmak yeterli:
#   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/hakan-svg/PKD-Post-Kreatif-Downloader/main/mac-kur.sh)"
set -e

DIZIN="${VIDEO_INDIRICI_DIZIN:-$HOME/video-indirici}"
DEPO="https://github.com/hakan-svg/PKD-Post-Kreatif-Downloader"

echo "==> PKD kuruluyor..."

# 1) Apple komut satırı araçları (python3 için gerekli)
if ! xcode-select -p >/dev/null 2>&1; then
  echo "==> Apple komut satırı araçları kuruluyor."
  echo "    Açılan pencerede 'Yükle'ye tıkla; bitince kurulum kendiliğinden sürer."
  xcode-select --install >/dev/null 2>&1 || true
  until xcode-select -p >/dev/null 2>&1; do sleep 10; done
fi

# 2) ffmpeg (görüntü ile sesi birleştirmek için)
if ! command -v ffmpeg >/dev/null 2>&1 \
   && [ ! -x /opt/homebrew/bin/ffmpeg ] && [ ! -x /usr/local/bin/ffmpeg ]; then
  BREW="$(command -v brew || true)"
  [ -z "$BREW" ] && [ -x /opt/homebrew/bin/brew ] && BREW=/opt/homebrew/bin/brew
  [ -z "$BREW" ] && [ -x /usr/local/bin/brew ] && BREW=/usr/local/bin/brew
  if [ -z "$BREW" ]; then
    echo "==> Homebrew kuruluyor (Mac şifreni sorabilir; yazarken görünmemesi normal)..."
    NONINTERACTIVE=1 /bin/bash -c \
      "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    [ -x /opt/homebrew/bin/brew ] && BREW=/opt/homebrew/bin/brew || BREW=/usr/local/bin/brew
  fi
  echo "==> ffmpeg kuruluyor (birkaç dakika sürebilir)..."
  "$BREW" install -q ffmpeg
fi

# 2b) İkonlu bildirimler için terminal-notifier (yoksa ikonsuz bildirime düşer)
if ! command -v terminal-notifier >/dev/null 2>&1; then
  BREW2="$(command -v brew || true)"
  [ -z "$BREW2" ] && [ -x /opt/homebrew/bin/brew ] && BREW2=/opt/homebrew/bin/brew
  [ -z "$BREW2" ] && [ -x /usr/local/bin/brew ] && BREW2=/usr/local/bin/brew
  [ -n "$BREW2" ] && "$BREW2" install -q terminal-notifier || true
fi

# 3) Programı indir (git gerekmez)
echo "==> Program indiriliyor: $DIZIN"
mkdir -p "$DIZIN"
curl -fsSL "$DEPO/archive/refs/heads/main.tar.gz" | tar xz -C "$DIZIN" --strip-components 1

# 4) Python ortamı
cd "$DIZIN"
python3 -m venv .venv
./.venv/bin/pip install -q -U "yt-dlp[default,curl-cffi]"

# 5) Otomatik başlatma kur + sunucuyu hemen başlat
./otomatik-baslat-kur.sh

# 6) Eklentiyi masaüstüne kopyala — Chrome'da seçilecek klasör bu.
#    (Yanlışlıkla ana klasörün seçilmesini önler; net isimli tek klasör.)
EKLENTI="$HOME/Desktop/PKD-Eklenti"
rm -rf "$EKLENTI"
cp -R "$DIZIN/eklenti" "$EKLENTI"
open -R "$EKLENTI" 2>/dev/null || true
osascript >/dev/null 2>&1 <<'AS' || true
tell application "Google Chrome"
  activate
  if (count of windows) = 0 then make new window
  set URL of active tab of front window to "chrome://extensions/"
end tell
AS

echo
echo "✅ Kurulum bitti. Sunucu çalışıyor ve bilgisayar her açıldığında kendiliğinden başlayacak."
echo
echo "Son adım — Chrome'da (30 saniye, bir kereliğine):"
echo "  1) Açılan chrome://extensions sayfasında sağ üstten 'Geliştirici modu'nu aç"
echo "  2) 'Paketlenmemiş öğe yükle'ye tıkla, MASAÜSTÜNDEKİ 'PKD-Eklenti' klasörünü seç"
echo
echo "Not: Masaüstündeki PKD-Eklenti klasörünü silme; Chrome eklentiyi oradan çalıştırır."
