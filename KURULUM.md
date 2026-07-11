# Sıfırdan Kurulum Rehberi

Bilgisayardan anlamayanlar için adım adım. Yaklaşık 5-10 dakika sürer.
Kurulum bir kere yapılır, sonrasında her şey tek tıkla çalışır.

---

## MAC KULLANIYORSAN

### 1. Terminal'i aç
Klavyede **Cmd + Boşluk** tuşlarına bas, açılan arama kutusuna
**Terminal** yaz, Enter'a bas. Siyah/beyaz bir yazı penceresi açılacak.
Korkma, sadece aşağıdakileri yapıştıracaksın.

### 2. Aşağıdaki TEK satırı KOPYALA, Terminal'e YAPIŞTIR, Enter'a bas

```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/hakan-svg/PKD-Post-Kreatif-Downloader/main/mac-kur.sh)"
```

Gerisini kurulum kendisi halleder. Sadece şunlar olabilir:

- Mac **"komut satırı araçları kurulsun mu?"** penceresi açarsa
  **Yükle**'ye tıkla ve bekle — kurulum kendiliğinden devam eder.
- **Şifreni sorarsa** yaz (yazarken ekranda görünmez, normaldir), Enter'a bas.
- **"Terminal, Chrome'u denetlemek istiyor"** diye sorarsa **Tamam**'a tıkla.

Sonunda **"✅ Kurulum bitti"** yazısını göreceksin; Chrome'da eklenti
sayfası, Finder'da da **eklenti** klasörü kendiliğinden açılır.
Terminal'i kapatabilirsin.

---

## WINDOWS KULLANIYORSAN

### 1. Python kur
https://www.python.org/downloads/ adresinden **Download Python**'a tıkla,
indirilen dosyayı aç. **ÖNEMLİ:** Kurulum ekranının en altındaki
**"Add python.exe to PATH"** kutusunu mutlaka İŞARETLE, sonra
**Install Now**'a tıkla.

### 2. ffmpeg kur
Başlat menüsüne **cmd** yaz, **Komut İstemi**'ni aç, şunu yapıştır, Enter:

```
winget install Gyan.FFmpeg
```

### 3. Programı indir
https://github.com/hakan-svg/PKD-Post-Kreatif-Downloader adresine gir →
yeşil **Code** düğmesi → **Download ZIP**. İnen ZIP'e sağ tıkla →
**Tümünü ayıkla** → çıkan **PKD-Post-Kreatif-Downloader** klasörünü
**Belgeler**'in içine taşı.

### 4. Kur
Klasörün içindeki **kur.bat** dosyasına çift tıkla, bitmesini bekle.
("Windows bilgisayarınızı korudu" uyarısı çıkarsa **Ek bilgi →
Yine de çalıştır**.) Sonra **otomatik-baslat-kur.bat**'a çift tıkla.
Son olarak **baslat.bat**'a çift tıkla (bir kereliğine; bundan sonra
bilgisayar her açıldığında kendiliğinden çalışır).

---

## CHROME EKLENTİSİNİ EKLE

1. Chrome'un adres çubuğuna şunu yaz, Enter'a bas: `chrome://extensions`
   (Mac'te kurulum bu sayfayı zaten kendisi açar)
2. Sağ üst köşedeki **Geliştirici modu** anahtarını aç (maviye dönsün)
3. Sol üstte beliren **Paketlenmemiş öğe yükle** düğmesine tıkla
4. Klasörü seç:
   - **Mac:** Kurulumun sonunda Finder'da işaretli açılan **PKD-Eklenti**
     klasörünü `chrome://extensions` sayfasının üzerine **sürükleyip bırak**
     — bu kadar. (Klasör güvenli bir sistem konumundadır, yanlışlıkla
     silinmez.)
   - **Windows:** **PKD-Post-Kreatif-Downloader** klasörünün İÇİNDEKİ **eklenti** klasörü
     — dikkat: ana klasörün kendisini değil, içindeki **eklenti**'yi
     seçmezsen "Manifest dosyası eksik" hatası alırsın
5. Araç çubuğunda puzzle (🧩) simgesine tıkla → **PKD**'nin
   yanındaki raptiyeye tıkla ki hep görünsün

---

## KULLANIM

1. Video olan herhangi bir sayfayı aç (YouTube, Twitter, Instagram…)
2. Fareyi videonun üzerine getir — videonun **sağ üst köşesinde** yuvarlak
   bir indirme düğmesi belirir
3. Düğmeye tıkla → kalite seçenekleri açılır (örn. **1080p**, **720p**,
   **Sadece ses**)
4. İstediğine tıkla → "İndirme başladı" yazısını görünce sayfayı, Chrome'u,
   her şeyi kapatabilirsin; indirme arka planda sürer
5. Video **İndirilenler / PKD** klasörüne iner; bitince Mac'te
   sağ üstte bildirim çıkar

Düğme çıkmayan bir sayfada araç çubuğundaki **PKD** simgesine
tıklayarak da indirebilirsin.

**Instagram gibi girişli siteler:** Chrome'da o siteye giriş yapmış
olman yeterli; başka bir şey yapmana gerek yok.

## KALDIRMAK İSTERSEN

**Mac:** Terminal'e şu tek satırı yapıştır (veya program klasöründeki
**kaldir.command**'a çift tıkla):

```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/hakan-svg/PKD-Post-Kreatif-Downloader/main/kaldir.command)"
```

**Windows:** Program klasöründeki **kaldir.bat**'a çift tıkla, sonra
klasörü çöpe taşı.

**İkisinde de son adım:** Chrome > `chrome://extensions` > PKD kartında
**Kaldır**'a tıkla (Chrome bunu dışarıdan yaptırmaz, elle gerekiyor).

İndirdiğin videolar silinmez; **İndirilenler / PKD** klasöründe kalır.

---

## SORUN OLURSA

- **"Yerel sunucu çalışmıyor" diyorsa:** PKD-Post-Kreatif-Downloader klasöründeki
  **baslat.command**'a (Mac) / **baslat.bat**'a (Windows) çift tıkla.
- **Video bulunamadı diyorsa:** sayfayı yenileyip videoyu bir kez
  oynatmayı dene, sonra tekrar simgeye tıkla.
