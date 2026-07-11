// Popup: sayfa içi düğmenin yedeği. İndirme sunucuda çalışır;
// popup kapatılsa da sürer, bitince macOS bildirimi gelir.
const $ = (id) => document.getElementById(id);
let sayfaUrl = "";

function mesaj(yazi, tur = "") {
  $("mesaj").textContent = yazi;
  $("mesaj").className = tur;
}

function mesajGonder(m) {
  return chrome.runtime.sendMessage(m).catch(() => ({ hata: "sunucu-yok" }));
}

function sureYaz(sn) {
  if (!sn) return "";
  const d = Math.floor(sn / 60), s = Math.round(sn % 60);
  return ` · ${d}:${String(s).padStart(2, "0")}`;
}

async function formatlariGetir() {
  $("icerik").innerHTML = '<span class="donen"></span> Video bilgisi alınıyor…';
  $("butonlar").textContent = "";
  mesaj("");
  const v = await mesajGonder({
    tip: "formatlar", url: sayfaUrl, cerez: $("cerez").checked,
  });
  $("icerik").textContent = "";
  if (v.hata) {
    return mesaj(v.hata === "sunucu-yok"
      ? "Yerel sunucu çalışmıyor.\nvideo-indirici klasöründeki baslat.command dosyasına çift tıkla."
      : "Video bulunamadı: " + v.hata, "hata");
  }

  $("baslik").hidden = false;
  $("baslik").textContent = v.baslik;
  $("meta").hidden = false;
  $("meta").textContent = (v.site || "") + sureYaz(v.sure);

  const ekle = (etiket, govde, birincil = false) => {
    const b = document.createElement("button");
    b.textContent = etiket;
    if (birincil) b.className = "birincil";
    b.onclick = () => indir(govde, etiket);
    $("butonlar").appendChild(b);
  };
  if (v.cozunurlukler.length) {
    v.cozunurlukler.forEach((h, i) => ekle(`${h}p`, { yukseklik: h }, i === 0));
  } else {
    ekle("En iyi kalite", {}, true);
  }
  ekle("Sadece ses", { sadeceSes: true });
}

async function indir(govde, etiket) {
  const y = await mesajGonder({
    tip: "indir", url: sayfaUrl, cerez: $("cerez").checked, ...govde,
  });
  if (y.hata) return mesaj(y.hata, "hata");
  mesaj(`✅ İndirme başladı (${etiket}).\nBitince bildirim gelecek; bu pencereyi ve sayfayı kapatabilirsin.\nDosya: İndirilenler/VideoIndirici`, "tamam");
}

(async () => {
  const { cerezTercihi } = await chrome.storage.local.get("cerezTercihi");
  $("cerez").checked = !!cerezTercihi;
  $("cerez").onchange = () => {
    chrome.storage.local.set({ cerezTercihi: $("cerez").checked });
    formatlariGetir();
  };

  const ping = await mesajGonder({ tip: "ping" });
  if (!ping.tamam) {
    $("icerik").textContent = "";
    return mesaj(
      "Yerel sunucu çalışmıyor.\nBaşlatmak için: video-indirici klasöründeki " +
      "baslat.command dosyasına çift tıkla.", "hata");
  }
  $("sunucuNokta").classList.add("acik");

  const [sekme] = await chrome.tabs.query({ active: true, currentWindow: true });
  sayfaUrl = sekme?.url || "";
  if (!/^https?:/.test(sayfaUrl)) {
    $("icerik").textContent = "";
    return mesaj("Bu sayfada indirilebilir video yok.", "hata");
  }
  formatlariGetir();
})();
