#!/bin/zsh
# PKD — Post Kreatif Downloader'ı Mac'ten tamamen kaldırır.
# Çift tıklayarak veya şu tek satırla çalıştırılabilir:
#   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/hakan-svg/PKD-Post-Kreatif-Downloader/main/kaldir.command)"
#
# İndirilen videolara DOKUNMAZ (~/Downloads/PKD durur).

kaldir() {
  echo "==> PKD kaldırılıyor..."

  # 1) Otomatik başlatmayı ve çalışan sunucuyu durdur
  launchctl unload "$HOME/Library/LaunchAgents/com.video-indirici.plist" 2>/dev/null
  rm -f "$HOME/Library/LaunchAgents/com.video-indirici.plist"
  kill $(lsof -ti :8765) 2>/dev/null

  # 2) Eklenti kopyaları (eski masaüstü konumu dahil) ve günlük dosyası
  rm -rf "$HOME/Library/Application Support/PKD"
  rm -rf "$HOME/Desktop/PKD-Eklenti" "$HOME/Desktop/VideoIndirici-Eklenti"
  rm -f /tmp/video-indirici.log

  # 3) Program klasörü
  cd "$HOME"
  rm -rf "$HOME/video-indirici"

  echo
  echo "✅ Kaldırıldı. Son bir adım kaldı (Chrome izin vermediği için elle):"
  echo "   Chrome > chrome://extensions > PKD kartında 'Kaldır'a tıkla."
  echo
  echo "İndirilen videoların duruyor: ~/Downloads/PKD — istersen elle silebilirsin."
}
kaldir
