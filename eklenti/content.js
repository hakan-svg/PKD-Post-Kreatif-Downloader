// Video İndirici — sayfadaki videoları bulur, üzerlerine indirme düğmesi koyar.
(() => {
  const EN_KUCUK_GENISLIK = 180; // küçük önizleme/avatar videolarını atla
  const dugmeler = new Map();     // video -> düğme
  let panel = null;

  const OK_SVG =
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
    'stroke-linecap="round" stroke-linejoin="round">' +
    '<path d="M12 4v11"/><path d="M8 11l4 4 4-4"/><path d="M5 20h14"/></svg>';

  function mesajGonder(m) {
    return chrome.runtime.sendMessage(m).catch(() => ({ hata: "sunucu-yok" }));
  }

  function dugmeOlustur(video) {
    const d = document.createElement("div");
    d.className = "vi-dugme";
    d.innerHTML = OK_SVG;
    d.title = "Videoyu indir";
    d.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      panelAc(d);
    });
    document.documentElement.appendChild(d);
    dugmeler.set(video, d);
  }

  function konumla() {
    for (const [video, d] of dugmeler) {
      if (!video.isConnected) {
        d.remove();
        dugmeler.delete(video);
        continue;
      }
      const r = video.getBoundingClientRect();
      if (r.width < EN_KUCUK_GENISLIK || r.height < 100 ||
          r.bottom < 0 || r.top > innerHeight) {
        d.classList.remove("vi-gorunur");
        continue;
      }
      d.style.top = Math.max(r.top + 10, 4) + "px";
      d.style.left = Math.min(r.right, innerWidth) - 44 + "px";
    }
  }

  // Düğme yalnızca imleç videonun üzerindeyken görünür
  document.addEventListener("mousemove", (e) => {
    for (const [video, d] of dugmeler) {
      const r = video.getBoundingClientRect();
      const ustunde =
        e.clientX >= r.left && e.clientX <= r.right &&
        e.clientY >= r.top && e.clientY <= r.bottom &&
        r.width >= EN_KUCUK_GENISLIK;
      d.classList.toggle("vi-gorunur", ustunde || d.contains(e.target));
    }
  }, { passive: true });

  function tara() {
    document.querySelectorAll("video").forEach((v) => {
      if (!dugmeler.has(v)) dugmeOlustur(v);
    });
    konumla();
  }

  function panelKapat() {
    if (panel) {
      panel.remove();
      panel = null;
    }
  }

  async function panelAc(dugme) {
    panelKapat();
    panel = document.createElement("div");
    panel.className = "vi-panel";
    const r = dugme.getBoundingClientRect();
    panel.style.top = Math.min(r.bottom + 8, innerHeight - 120) + "px";
    panel.style.left = Math.max(8, r.right - 270) + "px";
    panel.innerHTML =
      '<div class="vi-yukleniyor"><div class="vi-donen"></div>' +
      '<span class="vi-durum">Video bilgisi alınıyor…</span></div>';
    document.documentElement.appendChild(panel);

    const { cerezTercihi } = await chrome.storage.local.get("cerezTercihi");
    const cerez = !!cerezTercihi;
    const yanit = await mesajGonder({
      tip: "formatlar", url: location.href, ref: document.referrer, cerez,
    });
    if (!panel) return;
    if (yanit.hata) return hataGoster(yanit.hata);

    panel.textContent = "";
    const baslik = document.createElement("div");
    baslik.className = "vi-baslik";
    baslik.textContent = yanit.baslik || "Video";
    panel.appendChild(baslik);

    const kutu = document.createElement("div");
    kutu.className = "vi-secenekler";
    panel.appendChild(kutu);

    const ekle = (etiket, govde, birincil) => {
      const s = document.createElement("button");
      s.className = "vi-secenek" + (birincil ? " vi-birincil" : "");
      s.textContent = etiket;
      s.onclick = () => indir(govde, cerez);
      kutu.appendChild(s);
    };
    const cozunurlukler = yanit.cozunurlukler || [];
    if (cozunurlukler.length) {
      cozunurlukler.forEach((h, i) => ekle(h + "p", { yukseklik: h }, i === 0));
    } else {
      ekle("En iyi kalite", {}, true);
    }
    ekle("Sadece ses", { sadeceSes: true }, false);
  }

  function hataGoster(h) {
    if (!panel) return;
    const metin = h === "sunucu-yok"
      ? "Yerel sunucu çalışmıyor — video-indirici klasöründeki baslat.command'ı çalıştır."
      : "Video çözümlenemedi. Girişli içerikse eklenti menüsünden çerezleri açmayı dene.";
    panel.innerHTML = '<div class="vi-durum"></div>';
    panel.firstChild.textContent = metin;
    setTimeout(panelKapat, 6000);
  }

  async function indir(govde, cerez) {
    if (!panel) return;
    panel.innerHTML =
      '<div class="vi-tamam">⬇ İndirme başladı</div>' +
      '<div class="vi-durum" style="margin-top:4px">Bitince bildirim gelecek. ' +
      "Bu sayfayı kapatabilirsin.</div>";
    const y = await mesajGonder({
      tip: "indir", url: location.href, ref: document.referrer, cerez, ...govde,
    });
    if (y && y.hata) return hataGoster(y.hata);
    setTimeout(panelKapat, 3000);
  }

  document.addEventListener("click", (e) => {
    if (panel && !panel.contains(e.target)) panelKapat();
  }, true);
  addEventListener("scroll", () => { konumla(); panelKapat(); },
    { passive: true, capture: true });
  addEventListener("resize", konumla, { passive: true });

  setInterval(tara, 1200);
  tara();
})();
