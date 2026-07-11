#!/usr/bin/env python3
"""PKD — Post Kreatif Downloader, yerel sunucu.

Chrome eklentisinin arka ucu. Eklentiden gelen sayfa adresini yt-dlp ile
çözümler, mevcut çözünürlükleri döner ve seçilen kalitede indirir.

Uç noktalar:
    GET  /ping        sunucu ayakta mı
    GET  /isler       tüm indirmelerin durumu (yeniden eskiye)
    GET  /durum?id=   tek indirmenin durumu
    POST /formatlar   {url, ref, cerezler}                video bilgisi
    POST /indir       {url, ref, cerezler, yukseklik, sadeceSes, baslik}

Girişli siteler için eklenti, çerezleri Chrome API'siyle okuyup buraya
iletir; sunucu önce çerezsiz dener, olmazsa çerezlerle yeniden dener.
Anahtar zinciri (sistem şifresi) hiç kullanılmaz.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import yt_dlp

PORT = 8765
INDIRME_KLASORU = Path.home() / "Downloads" / "PKD"
FFMPEG = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
FFPROBE = shutil.which("ffprobe") or "/opt/homebrew/bin/ffprobe"
BILDIRICI = shutil.which("terminal-notifier")  # özel ikonlu bildirim için
BILDIRIM_IKONU = Path(__file__).parent / "bildirim-ikon.png"

# QuickTime/Önizleme'nin oynatabildiği kodekler
UYUMLU_VIDEO = {"h264", "hevc", "mpeg4", "prores"}
UYUMLU_SES = {"aac", "mp3", "alac", "pcm_s16le"}

ISLER: dict = {}  # is_id -> durum kaydı (ekleme sırası = zaman sırası)
KILIT = threading.Lock()


def temel_ayarlar(sayfa_url: str, ref: str = "", cerez_dosya=None) -> dict:
    ayar = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        # Alan adı kısıtlı embed'ler (ör. gömülü Vimeo) için üst sayfayı referer yap
        "http_headers": {"Referer": ref or sayfa_url},
        "ffmpeg_location": FFMPEG,
    }
    if cerez_dosya:
        ayar["cookiefile"] = cerez_dosya
    return ayar


def cerez_dosyasi(cerezler) -> str:
    """Eklentiden gelen çerez listesini Netscape biçimli geçici dosyaya yazar."""
    dosya = tempfile.NamedTemporaryFile(
        "w", suffix=".txt", prefix="pkd-cerez-", delete=False, encoding="utf-8")
    dosya.write("# Netscape HTTP Cookie File\n")
    for c in cerezler:
        alan = c.get("domain") or ""
        if not alan:
            continue
        if not c.get("hostOnly") and not alan.startswith("."):
            alan = "." + alan
        alt = "TRUE" if alan.startswith(".") else "FALSE"
        guvenli = "TRUE" if c.get("secure") else "FALSE"
        bitis = int(c.get("expirationDate") or 2147483647)
        dosya.write(f"{alan}\t{alt}\t{c.get('path', '/')}\t{guvenli}\t"
                    f"{bitis}\t{c.get('name', '')}\t{c.get('value', '')}\n")
    dosya.close()
    return dosya.name


def bildirim(metin: str) -> None:
    """İndirme bitince macOS bildirimi gösterir (eklenti/sayfa kapalı olsa da)."""
    if sys.platform != "darwin":
        return
    try:
        if BILDIRICI and BILDIRIM_IKONU.exists():
            subprocess.run(
                [BILDIRICI, "-title", "Post Kreatif Downloader", "-message", metin,
                 "-appIcon", str(BILDIRIM_IKONU), "-sound", "Glass"],
                capture_output=True, timeout=10)
        else:  # terminal-notifier yoksa ikonsuz sistem bildirimi
            metin = metin.replace('"', "'").replace("\\", "")
            subprocess.run(
                ["osascript", "-e",
                 f'display notification "{metin}" with title "Post Kreatif Downloader" sound name "Glass"'],
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


def quicktime_uyumlu_yap(dosya: str, is_id: str = "") -> str:
    """VP9/AV1/Opus gibi QuickTime'ın oynatamadığı kodekleri H.264/AAC mp4'e çevirir."""
    yol = Path(dosya)
    if not yol.exists() or yol.suffix.lower() not in {".mp4", ".mkv", ".webm", ".mov"}:
        return dosya
    video, ses = _kodekler(dosya)
    v_tamam = video is None or video in UYUMLU_VIDEO
    s_tamam = ses is None or ses in UYUMLU_SES
    if v_tamam and s_tamam and yol.suffix.lower() in {".mp4", ".mov"}:
        return dosya

    if is_id:
        with KILIT:
            ISLER[is_id]["durum"] = "donusturuluyor"
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


def secenek_listesi(bilgi: dict) -> list:
    """Kalite seçeneklerini üretir.

    Çoğu sitede yükseklik (720p, 1080p) bilinir. LinkedIn gibi bazı siteler
    yükseklik/kodek bilgisi vermez; orada bit hızına göre seçenek sunulur.
    """
    formatlar = [f for f in bilgi.get("formats", []) if f.get("vcodec") != "none"]
    yukseklikler = sorted({f["height"] for f in formatlar if f.get("height")},
                          reverse=True)
    if yukseklikler:
        return [{"etiket": f"{h}p", "yukseklik": h} for h in yukseklikler]

    hizli = sorted(
        ((f["format_id"], f["tbr"]) for f in formatlar
         if f.get("format_id") and f.get("tbr")),
        key=lambda x: -x[1],
    )
    adlar = ["Yüksek", "Orta", "Düşük"]
    secenekler = [
        {"etiket": f"{adlar[i]} ({tbr / 1000:.1f} Mbps)", "formatId": fid}
        for i, (fid, tbr) in enumerate(hizli[:3])
    ]
    return secenekler or [{"etiket": "En iyi kalite"}]


def _bilgi_cek(url: str, ref: str, cerez_dosya) -> dict:
    with yt_dlp.YoutubeDL(temel_ayarlar(url, ref, cerez_dosya)) as ydl:
        bilgi = ydl.extract_info(url, download=False)
    if bilgi.get("entries"):  # sayfada birden çok video/embed varsa ilkini al
        bilgi = next(e for e in bilgi["entries"] if e)
    return {
        "baslik": bilgi.get("title") or "video",
        "sure": bilgi.get("duration"),
        "kapak": bilgi.get("thumbnail"),
        "site": bilgi.get("extractor_key"),
        "secenekler": secenek_listesi(bilgi),
        "url": bilgi.get("webpage_url") or url,
    }


def formatlari_al(url: str, ref: str, cerezler) -> dict:
    try:
        return _bilgi_cek(url, ref, None)
    except Exception:
        if not cerezler:
            raise
        cd = cerez_dosyasi(cerezler)
        try:
            return _bilgi_cek(url, ref, cd)
        finally:
            os.unlink(cd)


def indirme_isi(is_id: str, istek: dict):
    url = istek["url"]
    ref = (istek.get("ref") or "").strip()
    yukseklik = istek.get("yukseklik")
    format_id = istek.get("formatId")
    sadece_ses = bool(istek.get("sadeceSes"))
    cerezler = istek.get("cerezler") or []
    baslik = istek.get("baslik") or url

    def kanca(d):
        with KILIT:
            iptal = ISLER[is_id].get("iptal")
        if iptal:
            raise yt_dlp.utils.DownloadCancelled("kullanıcı iptal etti")
        if d["status"] == "downloading":
            toplam = d.get("total_bytes") or d.get("total_bytes_estimate")
            with KILIT:
                ISLER[is_id]["durum"] = "indiriliyor"
                ISLER[is_id]["gecici"] = d.get("tmpfilename") or d.get("filename")
                if toplam:
                    ISLER[is_id]["yuzde"] = round(d["downloaded_bytes"] * 100 / toplam)

    def calistir(cerez_dosya):
        ayar = temel_ayarlar(url, ref, cerez_dosya)
        ayar.update({
            "outtmpl": str(INDIRME_KLASORU / "%(title).100s [%(id)s].%(ext)s"),
            "progress_hooks": [kanca],
            "merge_output_format": "mp4",
            "retries": 3,
        })
        if sadece_ses:
            ayar["format"] = "ba/b"
            ayar["postprocessors"] = [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3",
                 "preferredquality": "192"}]
        else:
            if format_id:  # yükseklik bilgisi olmayan siteler (ör. LinkedIn)
                ayar["format"] = f"{format_id}+ba/{format_id}/b"
            elif yukseklik:
                ayar["format"] = (f"bv*[height<={yukseklik}]+ba/"
                                  f"b[height<={yukseklik}]/bv*+ba/b")
            else:
                ayar["format"] = "bv*+ba/b"
            # Aynı çözünürlükte QuickTime uyumlu H.264/AAC'yi tercih et
            ayar["format_sort"] = ["res", "vcodec:h264", "acodec:aac"]
        with yt_dlp.YoutubeDL(ayar) as ydl:
            return ydl.extract_info(url, download=True)

    try:
        try:
            bilgi = calistir(None)
        except Exception:
            if not cerezler:
                raise
            cd = cerez_dosyasi(cerezler)
            try:
                bilgi = calistir(cd)
            finally:
                os.unlink(cd)
        if bilgi.get("entries"):
            bilgi = next(e for e in bilgi["entries"] if e)
        baslik = bilgi.get("title") or baslik
        with KILIT:
            ISLER[is_id]["baslik"] = baslik
        dosya = (bilgi.get("requested_downloads") or [{}])[0].get("filepath", "")
        if dosya and not sadece_ses:
            dosya = quicktime_uyumlu_yap(dosya, is_id)
        ad = Path(dosya).name if dosya else ""
        with KILIT:
            ISLER[is_id].update(durum="bitti", yuzde=100, dosya=ad)
        bildirim(f"İndirildi: {baslik}")
    except yt_dlp.utils.DownloadCancelled:
        with KILIT:
            ISLER[is_id]["durum"] = "iptal"
            gecici = ISLER[is_id].get("gecici")
        for kalinti in ([gecici, gecici + ".part"] if gecici else []):
            try:
                Path(kalinti).unlink(missing_ok=True)
            except Exception:
                pass
    except Exception as hata:
        with KILIT:
            ISLER[is_id].update(durum="hata", hata=str(hata)[:400])
        bildirim(f"İndirilemedi: {baslik}")


class Istekci(BaseHTTPRequestHandler):
    def log_message(self, *args):  # konsolu sessiz tut
        pass

    def _yanit(self, veri, kod: int = 200):
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
        elif yol.path == "/isler":
            with KILIT:
                liste = [{"id": i, **k} for i, k in ISLER.items()]
            self._yanit({"isler": list(reversed(liste[-20:]))})
        elif yol.path == "/durum":
            is_id = parse_qs(yol.query).get("id", [""])[0]
            with KILIT:
                kayit = ISLER.get(is_id)
            self._yanit(kayit or {"hata": "iş bulunamadı"}, 200 if kayit else 404)
        else:
            self._yanit({"hata": "bilinmeyen yol"}, 404)

    def do_POST(self):
        boy = int(self.headers.get("Content-Length", 0))
        try:
            istek = json.loads(self.rfile.read(boy) or b"{}")
        except json.JSONDecodeError:
            return self._yanit({"hata": "geçersiz JSON"}, 400)

        if self.path == "/iptal":
            is_id = istek.get("id") or ""
            with KILIT:
                kayit = ISLER.get(is_id)
                if kayit and kayit["durum"] in ("hazirlaniyor", "indiriliyor",
                                                "donusturuluyor"):
                    kayit["iptal"] = True
            return self._yanit({"tamam": bool(kayit)})

        if self.path == "/temizle":
            # Tamamlanmış/başarısız/iptal kayıtlarını geçmişten sil;
            # süren indirmelere dokunma. Tek bir id verilirse yalnızca onu sil.
            tek = istek.get("id")
            aktif = ("hazirlaniyor", "indiriliyor", "donusturuluyor")
            with KILIT:
                if tek:
                    if tek in ISLER and ISLER[tek]["durum"] not in aktif:
                        del ISLER[tek]
                else:
                    for i in [i for i, k in ISLER.items()
                              if k["durum"] not in aktif]:
                        del ISLER[i]
            return self._yanit({"tamam": True})

        url = (istek.get("url") or "").strip()
        if not url.startswith(("http://", "https://")):
            return self._yanit({"hata": "geçersiz adres"}, 400)

        if self.path == "/formatlar":
            try:
                self._yanit(formatlari_al(url, (istek.get("ref") or "").strip(),
                                          istek.get("cerezler") or []))
            except Exception as hata:
                self._yanit({"hata": str(hata)[:400]}, 500)
        elif self.path == "/indir":
            is_id = uuid.uuid4().hex[:12]
            with KILIT:
                ISLER[is_id] = {"durum": "hazirlaniyor", "yuzde": 0,
                                "baslik": istek.get("baslik") or url}
            threading.Thread(target=indirme_isi, args=(is_id, istek),
                             daemon=True).start()
            self._yanit({"id": is_id})
        else:
            self._yanit({"hata": "bilinmeyen yol"}, 404)


if __name__ == "__main__":
    INDIRME_KLASORU.mkdir(parents=True, exist_ok=True)
    print(f"PKD sunucusu: http://127.0.0.1:{PORT}")
    print(f"İndirme klasörü: {INDIRME_KLASORU}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Istekci).serve_forever()
