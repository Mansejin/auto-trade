(() => {
  const RANGE_KEY = "desk_equity_range";
  const BH_KEY = "desk_equity_bh";
  let range = localStorage.getItem(RANGE_KEY) || "30d";
  let bhOn = localStorage.getItem(BH_KEY) !== "0";
  let chart = null;
  let botSeries = null;
  let bhSeries = null;

  function money(v) {
    if (v == null || Number.isNaN(Number(v))) return "—";
    return `${Math.round(Number(v)).toLocaleString("ko-KR")}원`;
  }

  function setFreshness(kind, text) {
    const pulse = document.getElementById("pulse");
    const label = document.getElementById("fresh-text");
    if (label) label.textContent = text;
    if (pulse) {
      pulse.classList.toggle("stale", kind === "stale" || kind === "error");
      pulse.classList.toggle("ok", kind === "ok");
    }
  }

  function syncRangeUi() {
    document.querySelectorAll("[data-range]").forEach((btn) => {
      btn.classList.toggle("active", btn.getAttribute("data-range") === range);
    });
    const tog = document.getElementById("bh-toggle");
    if (tog) tog.checked = bhOn;
    document.querySelector(".lg-bh")?.classList.toggle("hidden", !bhOn);
  }

  function toChartTime(ts) {
    const s = String(ts || "");
    if (/^\d{4}-\d{2}-\d{2}$/.test(s)) {
      const d = Date.parse(s + "T00:00:00Z");
      return Number.isNaN(d) ? null : Math.floor(d / 1000);
    }
    const d = new Date(s);
    if (Number.isNaN(d.getTime())) return null;
    return Math.floor(d.getTime() / 1000);
  }

  function ensureChart() {
    if (typeof LightweightCharts === "undefined") {
      throw new Error("차트 라이브러리 미로드");
    }
    const el = document.getElementById("equity_chart");
    if (!el) return null;
    if (chart) return chart;
    chart = LightweightCharts.createChart(el, {
      autoSize: true,
      layout: {
        background: { color: "#131722" },
        textColor: "#9598a1",
        fontFamily: "에이투지체, system-ui, sans-serif",
      },
      grid: {
        vertLines: { color: "rgba(42, 46, 57, 0.6)" },
        horzLines: { color: "rgba(42, 46, 57, 0.6)" },
      },
      rightPriceScale: { borderColor: "#2a2e39" },
      timeScale: {
        borderColor: "#2a2e39",
        timeVisible: true,
        secondsVisible: false,
      },
    });
    botSeries = chart.addAreaSeries({
      lineColor: "#26a69a",
      topColor: "rgba(38, 166, 154, 0.35)",
      bottomColor: "rgba(38, 166, 154, 0.02)",
      lineWidth: 2,
      priceFormat: { type: "price", precision: 0, minMove: 1 },
    });
    bhSeries = chart.addLineSeries({
      color: "#9598a1",
      lineWidth: 2,
      lineStyle: LightweightCharts.LineStyle.Dashed,
      priceFormat: { type: "price", precision: 0, minMove: 1 },
    });
    return chart;
  }

  function seriesRows(points, key) {
    const rows = [];
    let lastT = null;
    for (const p of points) {
      if (p[key] == null) continue;
      const t = toChartTime(p.ts);
      const v = Number(p[key]);
      if (t == null || Number.isNaN(v)) continue;
      if (lastT != null && t < lastT) continue;
      if (t === lastT) rows[rows.length - 1] = { time: t, value: v };
      else {
        rows.push({ time: t, value: v });
        lastT = t;
      }
    }
    return rows;
  }

  function renderSummary(sum) {
    document.getElementById("eq-end").textContent = money(sum.end);
    document.getElementById("eq-start").textContent = money(sum.start);

    const retEl = document.getElementById("eq-ret");
    const ret = sum.ret_pct;
    if (ret == null) {
      retEl.textContent = "—";
      retEl.className = "v";
    } else {
      retEl.textContent = `${ret >= 0 ? "+" : ""}${Number(ret).toFixed(2)}%`;
      retEl.className = "v " + (ret >= 0 ? "ok" : "warn");
    }

    const bhEl = document.getElementById("eq-bh");
    if (!bhOn || sum.bh_ret_pct == null) {
      bhEl.textContent = "—";
      bhEl.className = "v";
    } else {
      const bh = Number(sum.bh_ret_pct);
      bhEl.textContent = `${bh >= 0 ? "+" : ""}${bh.toFixed(2)}%`;
      bhEl.className = "v " + (bh >= 0 ? "ok" : "warn");
    }

    const alphaEl = document.getElementById("eq-alpha");
    if (!bhOn || sum.alpha_pct == null) {
      alphaEl.textContent = "—";
      alphaEl.className = "v";
    } else {
      const a = Number(sum.alpha_pct);
      alphaEl.textContent = `${a >= 0 ? "+" : ""}${a.toFixed(2)}%p`;
      alphaEl.className = "v " + (a >= 0 ? "ok" : "warn");
    }

    const mddEl = document.getElementById("eq-mdd");
    mddEl.textContent = sum.mdd_pct != null ? `${Number(sum.mdd_pct).toFixed(2)}%` : "—";
    mddEl.className = "v warn";
  }

  async function refresh() {
    const base = window.__DESK_BASE__ || "/";
    const res = await fetch(
      `${base}api/equity?range=${encodeURIComponent(range)}&bh=${bhOn ? 1 : 0}`,
      { credentials: "same-origin" }
    );
    if (res.status === 401) {
      location.href = base;
      return;
    }
    if (!res.ok) throw new Error(`자산 API ${res.status}`);
    const data = await res.json();
    if (!data.ok && !(data.points && data.points.length)) {
      throw new Error(data.error || "자산 데이터 없음");
    }

    const points = data.points || [];
    const botRows = seriesRows(points, "equity");
    const bhRows = bhOn ? seriesRows(points, "bh_equity") : [];

    ensureChart();
    if (botSeries) botSeries.setData(botRows);
    if (bhSeries) bhSeries.setData(bhRows);
    if (chart) chart.timeScale().fitContent();

    renderSummary(data.summary || {});
    const bg =
      data.bitget_usdt != null
        ? ` · Bitget ${Number(data.bitget_usdt).toLocaleString("en-US", { maximumFractionDigits: 2 })} USDT`
        : "";
    document.getElementById("chart-meta").textContent =
      `${data.market || "KRW-BTC"} · ${data.range || range} · 포인트 ${botRows.length}${bg}`;
    document.getElementById("eq-source").textContent =
      data.source === "trades_mtm"
        ? "복원(체결+일봉)"
        : data.source === "history"
          ? "스냅샷"
          : data.source || "—";
    setFreshness(botRows.length ? "ok" : "stale", botRows.length ? "최신" : "데이터 부족");
  }

  async function loop() {
    try {
      await refresh();
    } catch (e) {
      console.error(e);
      setFreshness("error", `갱신 실패 · ${e.message || e}`);
    }
    setTimeout(loop, 60000);
  }

  document.querySelectorAll("[data-range]").forEach((btn) => {
    btn.addEventListener("click", () => {
      range = btn.getAttribute("data-range") || "30d";
      localStorage.setItem(RANGE_KEY, range);
      syncRangeUi();
      refresh().catch((e) => setFreshness("error", e.message || String(e)));
    });
  });
  document.getElementById("bh-toggle")?.addEventListener("change", (e) => {
    bhOn = Boolean(e.target.checked);
    localStorage.setItem(BH_KEY, bhOn ? "1" : "0");
    syncRangeUi();
    refresh().catch((err) => setFreshness("error", err.message || String(err)));
  });

  syncRangeUi();
  loop();
})();
