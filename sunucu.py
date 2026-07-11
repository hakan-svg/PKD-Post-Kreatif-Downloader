#!/usr/bin/env python3
"""Video İndirici — yerel sunucu.

Chrome eklentisinin arka ucu. Eklentiden gelen sayfa adresini yt-dlp ile
çözümler, mevcut çözünürlükleri döner ve seçilen kalitede indirir.

Uç noktalar:
    GET  /ping                       sunucu ayakta mı
    POST /formatlar {url, cerez}     video bilgisi + çözünürlük listesi
    POST /indir {url, yukseklik, sadeceSes, cerez}   indirmeyi başlat
    GET  /durum?id=...               indirme ilerlemesi
"""

import json
import shutil
import subprocess
import sys
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import yt_dlp

PORT = 8765
INDIRME_KLASORU = Path.home() / "Downloads" / "VideoIndirici"
FFMPEG = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
FFPROBE = shutil.which("ffprobe") or "/opt/homebrew/bin/ffprobe"

# QuickTime/Önizleme'nin oynatabildiği kodekler
UYUMLU_VIDEO = {"h264", "hevc", "mpeg4", "prores"}
UYUMLU_SES = {"aac", "mp3", "alac", "pcm_s16le"}

ISLER: dict[str, dict] = {}
KILIT = threading.Lock()


def temel_ayarlar(sayfa_url: str, cerez: bool, ref: str = "") -> dict:
    ayar = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        # Alan adı kısıtlı embed'ler (ör. gömülü Vimeo) için üst sayfayı referer yap
        "http_headers": {"Referer": ref or sayfa_url},
        "ffmpeg_location": FFMPEG,
    }
    if cerez:
        # Girişli içerik (Instagram, özel Twitter vb.) için Chrome çerezleri.
        # macOS ilk kullanımda anahtar zinciri izni sorabilir.
        ayar["cookiesfrombrowser"] = ("chrome",)
    return ayar


def bildirim(metin: str) -> None:
    """İndirme bitince macOS bildirimi gösterir (eklenti/sayfa kapalı olsa da)."""
    if sys.platform != "darwin":
        return
    try:
        metin = metin.replace('"', "'").replace("\\", "")
        subprocess.run(
            ["osascript", "-e",
             f'display notification "{metin}" with title "Video İndirici" sound name "Glass"'],
            capture_output=True, timeout=10)
    except Exception:
        pass


def _kodekler(dosya: str) -> tuple:
    try:
        c = subprocess.run(
            [FFPROBE, "-v", "error", "-show_entries", "stream=codec_type,codec_name",
             "-of", "json", dosya],
            capture_output=True, text=True, timeout=30)
        akislar = json.loads(c.stdout).get("streams", [])
        video = next((a.get("codec_name") for a in akislar
                      if a.get("codec_type") == "video"), None)
        ses = next((a.get("codec_name") for a in akislar
                    if a.get("codec_type") == "audio"), None)
        return video, ses
    except Exception:
        return None, None


def quicktime_uyumlu_yap(dosya: str) -> str:
    """VP9/AV1/Opus gibi QuickTime'ın oynatamadığı kodekleri H.264/AAC mp4'e çevirir."""
    yol = Path(dosya)
    if not yol.exists() or yol.suffix.lower() not in {".mp4", ".mkv", ".webm", ".mov"}:
        return dosya
    video, ses = _kodekler(dosya)
    v_tamam = video is None or video in UYUMLU_VIDEO
    s_tamam = ses is None or ses in UYUMLU_SES
    if v_tamam and s_tamam and yol.suffix.lower() in {".mp4", ".mov"}:
        return dosya

    ara = yol.parent / (yol.stem + ".uyumlu.mp4")
    komut = [FFMPEG, "-y", "-i", str(yol),
             "-c:v", "copy" if v_tamam else "libx264"]
    if not v_tamam:
        komut += ["-crf", "20", "-preset", "veryfast"]
    komut += ["-c:a", "copy" if s_tamam else "aac"]
    if not s_tamam:
        komut += ["-b:a", "192k"]
    komut += ["-movflags", "+faststart", str(ara)]
    sonuc = subprocess.run(komut, capture_output=True)
    if sonuc.returncode == 0 and ara.exists() and ara.stat().st_size > 0:
        yol.unlink()
        hedef = yol.with_suffix(".mp4")
        ara.rename(hedef)
        return str(hedef)
    ara.unlink(missing_ok=True)
    return dosya


def formatlari_al(url: str, cerez: bool, ref: str = "") -> dict:
    with yt_dlp.YoutubeDL(temel_ayarlar(url, cerez, ref)) as ydl:
        bilgi = ydl.extract_info(url, download=False)
    if bilgi.get("entries"):  # sayfada birden çok video/embed varsa ilkini al
        bilgi = next(e for e in bilgi["entries"] if e)
    yukseklikler = sorted(
        {f["height"] for f in bilgi.get("formats", [])
         if f.get("vcodec") not in (None, "none") and f.get("height")},
        reverse=True,
    )
    return {
        "baslik": bilgi.get("title") or "video",
        "sure": bilgi.get("duration"),
        "kapak": bilgi.get("thumbnail"),
        "site": bilgi.get("extractor_key"),
        "cozunurlukler": yukseklikler,
        "url": bilgi.get("webpage_url") or url,
    }


def indirme_isi(is_id: str, url: str, yukseklik, sadece_ses: bool,
                cerez: bool, ref: str = ""):
    ayar = temel_ayarlar(url, cerez, ref)
    ayar.update({
        "outtmpl": str(INDIRME_KLASORU / "%(title).100s [%(id)s].%(ext)s"),
        "merge_output_format": "mp4",
        "retries": 3,
    })
    if sadece_ses:
        ayar["format"] = "ba/b"
        ayar["postprocessors"] = [
            {"key": "FFmpegExtractAudio", "preferredcodec": "m4a"}]
    elif yukseklik:
        ayar["format"] = (f"bv*[height<={yukseklik}]+ba/"
                          f"b[height<={yukseklik}]/bv*+ba/b")
        # Aynı çözünürlükte QuickTime uyumlu H.264/AAC'yi tercih et
        ayar["format_sort"] = ["res", "vcodec:h264", "acodec:aac"]
    else:
        ayar["format"] = "bv*+ba/b"
        ayar["format_sort"] = ["res", "vcodec:h264", "acodec:aac"]

    try:
        with yt_dlp.YoutubeDL(ayar) as ydl:
            bilgi = ydl.extract_info(url, download=True)
        if bilgi.get("entries"):
            bilgi = next(e for e in bilgi["entries"] if e)
        dosya = (bilgi.get("requested_downloads") or [{}])[0].get("filepath", "")
        if dosya and not sadece_ses:
            dosya = quicktime_uyumlu_yap(dosya)
        ad = Path(dosya).name if dosya else ""
        with KILIT:
            ISLER[is_id].update(durum="bitti", yuzde=100, dosya=ad)
        bildirim(f"İndirildi: {ad}" if ad else "İndirme tamamlandı")
    except Exception as hata:
        with KILIT:
            ISLER[is_id].update(durum="hata", hata=str(hata)[:400])
        bildirim("İndirilemedi — ayrıntı için eklentiye tıkla")


class Istekci(BaseHTTPRequestHandler):
    def log_message(self, *args):  # konsolu sessiz tut
        pass

    def _yanit(self, veri: dict, kod: int = 200):
        govde = json.dumps(veri).encode()
        self.send_response(kod)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(govde)))
        self.end_headers()
        self.wfile.write(govde)

    def do_OPTIONS(self):
        self._yanit({})

    def do_GET(self):
        yol = urlparse(self.path)
        if yol.path == "/ping":
            self._yanit({"tamam": True})
        elif yol.path == "/durum":
            is_id = parse_qs(yol.query).get("id", [""])[0]
            with KILIT:
                is_kaydi = ISLER.get(is_id)
            if is_kaydi:
                self._yanit(is_kaydi)
            else:
                self._yanit({"hata": "iş bulunamadı"}, 404)
        else:
            self._yanit({"hata": "bilinmeyen yol"}, 404)

    def do_POST(self):
        boy = int(self.headers.get("Content-Length", 0))
        try:
            istek = json.loads(self.rfile.read(boy) or b"{}")
        except json.JSONDecodeError:
            return self._yanit({"hata": "geçersiz JSON"}, 400)
        url = (istek.get("url") or "").strip()
        cerez = bool(istek.get("cerez"))
        if not url.startswith(("http://", "https://")):
            return self._yanit({"hata": "geçersiz adres"}, 400)

        ref = (istek.get("ref") or "").strip()

        if self.path == "/formatlar":
            try:
                self._yanit(formatlari_al(url, cerez, ref))
            except Exception as hata:
                self._yanit({"hata": str(hata)[:400]}, 500)
        elif self.path == "/indir":
            is_id = uuid.uuid4().hex[:12]
            with KILIT:
                ISLER[is_id] = {"durum": "hazirlaniyor", "yuzde": 0}
            threading.Thread(
                target=indirme_isi,
                args=(is_id, url, istek.get("yukseklik"),
                      bool(istek.get("sadeceSes")), cerez, ref),
                daemon=True,
            ).start()
            self._yanit({"id": is_id})
        else:
            self._yanit({"hata": "bilinmeyen yol"}, 404)


if __name__ == "__main__":
    INDIRME_KLASORU.mkdir(parents=True, exist_ok=True)
    print(f"Video İndirici sunucusu: http://127.0.0.1:{PORT}")
    print(f"İndirme klasörü: {INDIRME_KLASORU}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Istekci).serve_forever()
