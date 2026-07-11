// Yerel sunucuyla tüm konuşma burada yapılır; içerik betikleri sayfa
// kısıtlamalarına (CSP/CORS) takılmasın diye istekleri buraya yollar.
const SUNUCU = "http://127.0.0.1:8765";

chrome.runtime.onMessage.addListener((mesaj, gonderen, yanitla) => {
  (async () => {
    try {
      if (mesaj.tip === "ping") {
        const y = await fetch(`${SUNUCU}/ping`, { signal: AbortSignal.timeout(2000) });
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
          cerez: !!mesaj.cerez,
          yukseklik: mesaj.yukseklik,
          sadeceSes: !!mesaj.sadeceSes,
        }),
      });
      yanitla(await y.json());
    } catch {
      yanitla({ hata: "sunucu-yok" });
    }
  })();
  return true; // yanıt asenkron gelecek
});
