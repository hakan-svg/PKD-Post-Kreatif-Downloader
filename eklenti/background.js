// PKD — yerel sunucuyla tüm konuşma burada yapılır. Girişli siteler için
// çerezler Chrome API'siyle okunur (sistem şifresi/anahtar zinciri gerekmez)
// ve sunucuya iletilir; sunucu onları yalnızca gerekirse kullanır.
const SUNUCU = "http://127.0.0.1:8765";

// İki parçalı üst alan adları (co.uk, com.tr gibi) için kaba liste
const IKINCIL = new Set(["co", "com", "net", "org", "gov", "edu", "ac", "gen", "web"]);

function tabanAlan(url) {
  try {
    const parcalar = new URL(url).hostname.replace(/^www\./, "").split(".");
    if (parcalar.length <= 2) return parcalar.join(".");
    if (IKINCIL.has(parcalar[parcalar.length - 2])) {
      return parcalar.slice(-3).join(".");
    }
    return parcalar.slice(-2).join(".");
  } catch {
    return "";
  }
}

async function cerezleriTopla(url) {
  const taban = tabanAlan(url);
  if (!taban) return [];
  const alanlar = new Set([taban]);
  if (taban.includes("youtube")) alanlar.add("google.com"); // YouTube girişi Google'da
  let hepsi = [];
  for (const alan of alanlar) {
    try {
      hepsi = hepsi.concat(await chrome.cookies.getAll({ domain: alan }));
    } catch { /* izin yoksa çerezsiz devam */ }
  }
  return hepsi.map((c) => ({
    domain: c.domain, path: c.path, name: c.name, value: c.value,
    secure: c.secure, hostOnly: c.hostOnly, expirationDate: c.expirationDate,
  }));
}

chrome.runtime.onMessage.addListener((mesaj, gonderen, yanitla) => {
  (async () => {
    try {
      if (mesaj.tip === "ping") {
        const y = await fetch(`${SUNUCU}/ping`, { signal: AbortSignal.timeout(2000) });
        yanitla(await y.json());
        return;
      }
      if (mesaj.tip === "isler") {
        const y = await fetch(`${SUNUCU}/isler`, { signal: AbortSignal.timeout(2000) });
        yanitla(await y.json());
        return;
      }
      if (mesaj.tip === "iptal" || mesaj.tip === "temizle") {
        const y = await fetch(`${SUNUCU}/${mesaj.tip}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ id: mesaj.id }),
        });
        yanitla(await y.json());
        return;
      }
      const yol = mesaj.tip === "formatlar" ? "/formatlar" : "/indir";
      const y = await fetch(SUNUCU + yol, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: mesaj.url,
          ref: mesaj.ref || "",
          cerezler: await cerezleriTopla(mesaj.url),
          yukseklik: mesaj.yukseklik,
          formatId: mesaj.formatId,
          sadeceSes: !!mesaj.sadeceSes,
          baslik: mesaj.baslik || "",
        }),
      });
      yanitla(await y.json());
    } catch {
      yanitla({ hata: "sunucu-yok" });
    }
  })();
  return true; // yanıt asenkron gelecek
});
