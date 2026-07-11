# Video İndirici

Chrome eklentisi + yerel yt-dlp sunucusu. Açık sekmedeki videoyu çözünürlük
seçerek tek tıkla indirir. yt-dlp'nin desteklediği tüm siteler çalışır
(YouTube, Twitter/X, Instagram, Vimeo, TikTok ve 1800+ site).

**Mimari:** Eklenti sadece arayüzdür; indirme işini bilgisayarında çalışan
küçük bir yerel sunucu (`sunucu.py`, port 8765) yapar. Video akışlarını
çözmek ve ses+görüntüyü birleştirmek tarayıcı içinde mümkün olmadığı için
bu ikili yapı gereklidir.

## Kurulum

> Bilgisayardan anlamayanlar için adım adım anlatım: **[KURULUM.md](KURULUM.md)**

Gereksinimler: Python 3.10+, ffmpeg, Google Chrome.

**macOS (tek komut — ffmpeg, otomatik başlatma dahil her şeyi kurar):**
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/hakan-svg/video-indirici/main/mac-kur.sh)"
```

**Linux:**
```bash
git clone https://github.com/hakan-svg/video-indirici.git && cd video-indirici
./kur.sh
```

**Windows:** repoyu indir, `kur.bat`'a çift tıkla.

**Eklenti (tüm platformlar):**
1. Chrome'da `chrome://extensions` aç
2. Sağ üstten **Geliştirici modu**'nu aç
3. **Paketlenmemiş öğe yükle** → `eklenti` klasörünü seç

> Not: Chrome, Web Store dışından .crx paketi kurulumına izin vermediği ve
> Web Store video indiricileri kabul etmediği için eklenti bu şekilde
> "paketlenmemiş" yüklenir. Her bilgisayarda bir kez yapılır.

**Otomatik başlatma (önerilir):** `otomatik-baslat-kur.sh` (Mac) veya
`otomatik-baslat-kur.bat` (Windows) çalıştır — sunucu her oturum açılışında
kendiliğinden başlar, bir daha elle başlatman gerekmez.

## Kullanım

1. Sunucuyu başlat: otomatik başlatma kurduysan hiçbir şey yapma;
   kurmadıysan `baslat.command` (Mac) / `baslat.bat` (Windows)
2. Fareyi videonun üzerine getir, sağ üstte çıkan düğmeye tıkla
   (veya araç çubuğundaki eklenti simgesini kullan)
3. Çözünürlüğü seç → dosya `~/Downloads/VideoIndirici/` klasörüne iner;
   sayfa/Chrome kapatılabilir, bitince macOS bildirimi gelir

İndirilen dosyalar QuickTime/Önizleme uyumludur: H.264/AAC tercih edilir,
uyumsuz kodekler (VP9/AV1/Opus) otomatik dönüştürülür.

Girişli içerik (Instagram, gizli hesaplar) için popup'taki
"Chrome çerezlerini kullan" kutusunu işaretle.

## Notlar

- Sunucu yalnızca 127.0.0.1'i dinler; dışarıya kapalıdır.
- Bulut sunucuda (Railway vb.) çalıştırmak önerilmez: YouTube/Instagram
  datacenter IP'lerini engeller, dosyalar sunucu diskine iner ve çerez
  özelliği çalışmaz.
- Kişisel kullanım içindir; indirdiğin içeriğin telif koşullarına uymak
  sana aittir.
