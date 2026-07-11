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
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import yt_dlp

PORT = 8765
INDIRME_KLASORU = Path.home() / "Downloads" / "VideoIndirici"
FFMPEG = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"

ISLER: dict[str, dict] = {}
KILIT = threading.Lock()


def temel_ayarlar(sayfa_url: str, cerez: bool) -> dict:
    ayar = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        # Alan adı kısıtlı embed'ler (ör. gömülü Vimeo) için sayfayı referer yap
        "http_headers": {"Referer": sayfa_url},
        "ffmpeg_location": FFMPEG,
    }
    if cerez:
        # Girişli içerik (Instagram, özel Twitter vb.) için Chrome çerezleri.
        # macOS ilk kullanımda anahtar zinciri izni sorabilir.
        ayar["cookiesfrombrowser"] = ("chrome",)
    return ayar


def formatlari_al(url: str, cerez: bool) -> dict:
    with yt_dlp.YoutubeDL(temel_ayarlar(url, cerez)) as ydl:
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


def indirme_isi(is_id: str, url: str, yukseklik, sadece_ses: bool, cerez: bool):
    def kanca(d):
        if d["status"] == "downloading":
            toplam = d.get("total_bytes") or d.get("total_bytes_estimate")
            with KILIT:
                ISLER[is_id]["durum"] = "indiriliyor"
                if toplam:
                    ISLER[is_id]["yuzde"] = round(d["downloaded_bytes"] * 100 / toplam)

    ayar = temel_ayarlar(url, cerez)
    ayar.update({
        "outtmpl": str(INDIRME_KLASORU / "%(title).100s [%(id)s].%(ext)s"),
        "progress_hooks": [kanca],
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
    else:
        ayar["format"] = "bv*+ba/b"

    try:
        with yt_dlp.YoutubeDL(ayar) as ydl:
            bilgi = ydl.extract_info(url, download=True)
        if bilgi.get("entries"):
            bilgi = next(e for e in bilgi["entries"] if e)
        dosya = (bilgi.get("requested_downloads") or [{}])[0].get("filepath", "")
        with KILIT:
            ISLER[is_id].update(durum="bitti", yuzde=100,
                                dosya=Path(dosya).name if dosya else "")
    except Exception as hata:
        with KILIT:
            ISLER[is_id].update(durum="hata", hata=str(hata)[:400])


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

        if self.path == "/formatlar":
            try:
                self._yanit(formatlari_al(url, cerez))
            except Exception as hata:
                self._yanit({"hata": str(hata)[:400]}, 500)
        elif self.path == "/indir":
            is_id = uuid.uuid4().hex[:12]
            with KILIT:
                ISLER[is_id] = {"durum": "hazirlaniyor", "yuzde": 0}
            threading.Thread(
                target=indirme_isi,
                args=(is_id, url, istek.get("yukseklik"),
                      bool(istek.get("sadeceSes")), cerez),
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
