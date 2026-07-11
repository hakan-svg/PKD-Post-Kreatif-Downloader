#!/usr/bin/env python3
"""logo.png'den eklenti ve bildirim ikonlarını üretir.

Tasarım: PKD mavi→mor degrade, yuvarlatılmış kare zemin, beyaz uçak.
Çalıştırma: ./.venv/bin/python ikon-uret.py
"""

from pathlib import Path

from PIL import Image, ImageDraw

KOK = Path(__file__).parent
S = 1024
MAVI, MOR = (10, 132, 255), (191, 90, 242)

logo = Image.open(KOK / "logo.png").convert("RGBA")
maske = logo.split()[3]
maske = maske.crop(maske.getbbox())  # boşlukları kırp

# Degrade zemin (küçük çiz, büyüt: pürüzsüz olur)
kucuk = Image.new("RGB", (64, 64))
for y in range(64):
    for x in range(64):
        t = (x + y) / 126
        kucuk.putpixel((x, y), tuple(
            round(a + (b - a) * t) for a, b in zip(MAVI, MOR)))
zemin = kucuk.resize((S, S), Image.LANCZOS).convert("RGBA")

# Yuvarlatılmış kare (macOS oranı ~%22,5 köşe yarıçapı)
kose = Image.new("L", (S, S), 0)
ImageDraw.Draw(kose).rounded_rectangle([0, 0, S - 1, S - 1],
                                       radius=int(S * 0.225), fill=255)
zemin.putalpha(kose)

# Beyaz uçağı ortala (%60 genişlik)
hedef_gen = int(S * 0.60)
oran = hedef_gen / maske.width
uçak_maske = maske.resize((hedef_gen, int(maske.height * oran)), Image.LANCZOS)
beyaz = Image.new("RGBA", uçak_maske.size, (255, 255, 255, 255))
beyaz.putalpha(uçak_maske)
zemin.alpha_composite(beyaz, ((S - beyaz.width) // 2, (S - beyaz.height) // 2))

for boy in (16, 32, 48, 128):
    zemin.resize((boy, boy), Image.LANCZOS).save(KOK / "eklenti" / f"icon{boy}.png")
zemin.resize((256, 256), Image.LANCZOS).save(KOK / "bildirim-ikon.png")
print("ikonlar üretildi")
