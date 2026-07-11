// PKD popup: üstte açık sekmedeki video, altta indirme listesi.
// İndirmeler sunucuda çalışır; popup yalnızca durumu gösterir.
const $ = (id) => document.getElementById(id);
let sayfaUrl = "";
let videoBaslik = "";

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
  const v = await mesajGonder({ tip: "formatlar", url: sayfaUrl });
  $("icerik").textContent = "";
  if (v.hata) {
    return mesaj(v.hata === "sunucu-yok"
      ? "Yerel sunucu çalışmıyor.\nPKD klasöründeki baslat.command dosyasına çift tıkla."
      : "Bu sayfada indirilebilir video bulunamadı.", "hata");
  }
  videoBaslik = v.baslik || "";
  $("baslik").hidden = false;
  $("baslik").textContent = v.baslik;
  $("meta").hidden = false;
  $("meta").textContent = (v.site || "") + sureYaz(v.sure);

  const ekle = (etiket, govde, birincil = false) => {
    const b = document.createElement("button");
    b.textContent = etiket;
    if (birincil) b.className = "birincil";
    b.onclick = () => indir(govde);
    $("butonlar").appendChild(b);
  };
  (v.secenekler || [{ etiket: "En iyi kalite" }]).forEach((s, i) => {
    const { etiket, ...govde } = s;
    ekle(etiket, govde, i === 0);
  });
  ekle("Sadece ses (MP3)", { sadeceSes: true });
}

async function indir(govde) {
  const y = await mesajGonder({
    tip: "indir", url: sayfaUrl, baslik: videoBaslik, ...govde,
  });
  if (y.hata) return mesaj("İndirme başlatılamadı.", "hata");
  mesaj("İndirme başladı — bu pencereyi kapatabilirsin.", "tamam");
  isleriYenile();
}

function durumYaz(k) {
  if (k.durum === "bitti") return ["İndirildi ✓", "tamam"];
  if (k.durum === "hata") return ["Başarısız", "hata"];
  if (k.durum === "iptal") return ["İptal edildi", ""];
  if (k.durum === "donusturuluyor") return ["Dönüştürülüyor…", ""];
  if (k.durum === "indiriliyor") return [`%${k.yuzde || 0}`, ""];
  return ["Hazırlanıyor…", ""];
}

const AKTIF = new Set(["hazirlaniyor", "indiriliyor", "donusturuluyor"]);

async function isleriYenile() {
  const y = await mesajGonder({ tip: "isler" });
  if (y.hata) return;
  const liste = $("isListesi");
  liste.textContent = "";
  for (const k of y.isler || []) {
    const kutu = document.createElement("div");
    kutu.className = "is";

    const ust = document.createElement("div");
    ust.className = "is-ust";
    const ad = document.createElement("div");
    ad.className = "is-baslik";
    ad.textContent = k.baslik || k.dosya || "Video";
    ad.title = ad.textContent;
    const [durumMetni, durumSinifi] = durumYaz(k);
    const durum = document.createElement("div");
    durum.className = "is-durum " + durumSinifi;
    durum.textContent = durumMetni;
    ust.append(ad, durum);
    const dugme = document.createElement("button");
    dugme.className = "is-iptal";
    dugme.textContent = "✕";
    if (AKTIF.has(k.durum)) {
      dugme.title = "İptal et";
      dugme.onclick = async () => {
        dugme.disabled = true;
        await mesajGonder({ tip: "iptal", id: k.id });
        isleriYenile();
      };
    } else {
      dugme.title = "Listeden kaldır";
      dugme.onclick = async () => {
        dugme.disabled = true;
        await mesajGonder({ tip: "temizle", id: k.id });
        isleriYenile();
      };
    }
    ust.appendChild(dugme);
    kutu.appendChild(ust);

    if (AKTIF.has(k.durum)) {
      const cubuk = document.createElement("div");
      cubuk.className = "cubuk";
      const ic = document.createElement("div");
      ic.style.width = (k.durum === "donusturuluyor" ? 100 : k.yuzde || 0) + "%";
      cubuk.appendChild(ic);
      kutu.appendChild(cubuk);
    }
    liste.appendChild(kutu);
  }
}

(async () => {
  const ping = await mesajGonder({ tip: "ping" });
  if (!ping.tamam) {
    $("icerik").textContent = "";
    return mesaj(
      "Yerel sunucu çalışmıyor.\nBaşlatmak için bilgisayarı yeniden başlat " +
      "veya PKD klasöründeki baslat.command dosyasına çift tıkla.", "hata");
  }
  $("sunucuNokta").classList.add("acik");

  $("temizle").onclick = async () => {
    $("temizle").disabled = true;
    await mesajGonder({ tip: "temizle" });
    await isleriYenile();
    $("temizle").disabled = false;
  };

  isleriYenile();
  setInterval(isleriYenile, 1000);

  const [sekme] = await chrome.tabs.query({ active: true, currentWindow: true });
  sayfaUrl = sekme?.url || "";
  if (!/^https?:/.test(sayfaUrl)) {
    $("icerik").textContent = "";
    return mesaj("Bu sayfada video yok.", "");
  }
  formatlariGetir();
})();
