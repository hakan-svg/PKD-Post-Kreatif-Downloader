const SUNUCU = "http://127.0.0.1:8765";

const $ = (id) => document.getElementById(id);
let sayfaUrl = "";

function mesaj(yazi, tur = "") {
  $("mesaj").textContent = yazi;
  $("mesaj").className = tur;
}

async function sunucuAyaktaMi() {
  try {
    const y = await fetch(`${SUNUCU}/ping`, { signal: AbortSignal.timeout(2000) });
    return (await y.json()).tamam === true;
  } catch {
    return false;
  }
}

function sureYaz(sn) {
  if (!sn) return "";
  const d = Math.floor(sn / 60), s = Math.round(sn % 60);
  return ` · ${d}:${String(s).padStart(2, "0")}`;
}

async function formatlariGetir() {
  $("icerik").innerHTML = '<span class="donen"></span> Video bilgisi alınıyor…';
  $("butonlar").textContent = "";
  const cerez = $("cerez").checked;
  try {
    const y = await fetch(`${SUNUCU}/formatlar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: sayfaUrl, cerez }),
    });
    const v = await y.json();
    if (v.hata) throw new Error(v.hata);

    $("icerik").textContent = "";
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
  } catch (h) {
    $("icerik").textContent = "";
    mesaj("Video bulunamadı: " + h.message, "hata");
  }
}

async function indir(govde, etiket) {
  mesaj(`İndirme başlatıldı (${etiket})…`);
  const y = await fetch(`${SUNUCU}/indir`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url: sayfaUrl, cerez: $("cerez").checked, ...govde }),
  });
  const { id, hata } = await y.json();
  if (hata) return mesaj(hata, "hata");
  await chrome.storage.local.set({ aktifIs: id });
  ilerlemeIzle(id);
}

async function ilerlemeIzle(id) {
  $("cubuk").style.display = "block";
  const sayac = setInterval(async () => {
    let d;
    try {
      d = await (await fetch(`${SUNUCU}/durum?id=${id}`)).json();
    } catch {
      clearInterval(sayac);
      return mesaj("Sunucu bağlantısı koptu.", "hata");
    }
    $("cubukIc").style.width = (d.yuzde || 0) + "%";
    if (d.durum === "bitti") {
      clearInterval(sayac);
      chrome.storage.local.remove("aktifIs");
      mesaj(`✅ İndirildi: ${d.dosya}\n(Downloads/VideoIndirici)`, "tamam");
    } else if (d.durum === "hata") {
      clearInterval(sayac);
      chrome.storage.local.remove("aktifIs");
      mesaj("Hata: " + d.hata, "hata");
    } else {
      mesaj(`İndiriliyor… %${d.yuzde || 0}`);
    }
  }, 1000);
}

(async () => {
  // çerez tercihini hatırla
  const { cerezTercihi } = await chrome.storage.local.get("cerezTercihi");
  $("cerez").checked = !!cerezTercihi;
  $("cerez").onchange = () => {
    chrome.storage.local.set({ cerezTercihi: $("cerez").checked });
    formatlariGetir();
  };

  if (!(await sunucuAyaktaMi())) {
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

  // yarım kalan indirme varsa göster
  const { aktifIs } = await chrome.storage.local.get("aktifIs");
  if (aktifIs) ilerlemeIzle(aktifIs);

  formatlariGetir();
})();
