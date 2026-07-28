(() => {
  const SIGNAL_KO = {
    hold: "관망",
    buy: "매수",
    sell: "매도",
    stop_loss: "손절",
    take_profit: "익절",
    error: "오류",
    unknown: "—",
  };

  const REGIME_CLASS = {
    bull: "regime-bull",
    bear: "regime-bear",
    sideways: "regime-sideways",
    transition: "regime-transition",
  };

  const CHART_KEY = "desk_chart_mode";
  let chartMode = localStorage.getItem(CHART_KEY) || "upbit";
  let tvWidget = null;
  let lastTvKey = "";
  let lwChart = null;
  let lwSeries = null;
  let lastCandleKey = "";
  let lastStatus = null;

  function money(v) {
    if (v == null || Number.isNaN(Number(v))) return "—";
    return `${Math.round(Number(v)).toLocaleString("ko-KR")}원`;
  }

  function qty(v) {
    if (v == null || Number.isNaN(Number(v))) return "—";
    return Number(v)
      .toFixed(8)
      .replace(/\.?0+$/, "");
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

  function syncToggleUi() {
    document.getElementById("btn-upbit").classList.toggle("active", chartMode === "upbit");
    document.getElementById("btn-tv").classList.toggle("active", chartMode === "tv");
    document.getElementById("upbit_chart").classList.toggle("hidden", chartMode !== "upbit");
    document.getElementById("tv_chart").classList.toggle("hidden", chartMode !== "tv");
    document.querySelector(".chart-legend").classList.toggle("hidden", chartMode !== "upbit");
  }

  function setChartMode(mode) {
    if (mode !== "upbit" && mode !== "tv") return;
    chartMode = mode;
    localStorage.setItem(CHART_KEY, mode);
    syncToggleUi();
    if (lastStatus) {
      updateCharts(lastStatus).catch((e) => console.warn(e));
    }
  }

  function ensureTvChart(symbol, interval) {
    if (typeof TradingView === "undefined" || !TradingView.widget) {
      throw new Error("TradingView 스크립트 미로드");
    }
    const key = `${symbol}|${interval}`;
    if (key === lastTvKey && tvWidget) return;
    lastTvKey = key;
    const el = document.getElementById("tv_chart");
    if (!el) return;
    el.innerHTML = "";
    tvWidget = new TradingView.widget({
      autosize: true,
      symbol,
      interval: String(interval || "60"),
      timezone: "Asia/Seoul",
      theme: "dark",
      style: "1",
      locale: "kr",
      toolbar_bg: "#131722",
      enable_publishing: false,
      hide_top_toolbar: false,
      hide_legend: false,
      allow_symbol_change: false,
      save_image: false,
      container_id: "tv_chart",
      backgroundColor: "#131722",
      gridColor: "rgba(42, 46, 57, 0.6)",
    });
  }

  function destroyUpbitChart() {
    if (lwChart) {
      lwChart.remove();
      lwChart = null;
      lwSeries = null;
    }
    lastCandleKey = "";
  }

  function ensureUpbitChart() {
    if (typeof LightweightCharts === "undefined") {
      throw new Error("업비트 차트 라이브러리 미로드");
    }
    const el = document.getElementById("upbit_chart");
    if (!el) return null;
    if (lwChart) return lwChart;
    lwChart = LightweightCharts.createChart(el, {
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
      crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
      rightPriceScale: { borderColor: "#2a2e39" },
      timeScale: {
        borderColor: "#2a2e39",
        timeVisible: true,
        secondsVisible: false,
      },
    });
    lwSeries = lwChart.addCandlestickSeries({
      upColor: "#ef5350",
      downColor: "#2962ff",
      borderUpColor: "#ef5350",
      borderDownColor: "#2962ff",
      wickUpColor: "#ef5350",
      wickDownColor: "#2962ff",
    });
    return lwChart;
  }

  async function refreshUpbitChart() {
    const base = window.__DESK_BASE__ || "/";
    const res = await fetch(base + "api/candles", { credentials: "same-origin" });
    if (res.status === 401) {
      location.href = base;
      return;
    }
    if (!res.ok) throw new Error(`캔들 API ${res.status}`);
    const data = await res.json();
    const candles = data.candles || [];
    const markers = data.markers || [];
    const key = `${data.market}|${data.timeframe}|${candles.length}|${markers.length}|${
      candles.length ? candles[candles.length - 1].time : 0
    }`;

    document.getElementById("chart-meta").textContent = `${data.market || "—"} · ${
      data.timeframe || "—"
    } · 봉 ${candles.length}`;

    ensureUpbitChart();
    if (!lwSeries) return;

    if (key !== lastCandleKey) {
      lwSeries.setData(candles);
      lwSeries.setMarkers(markers);
      if (lwChart) lwChart.timeScale().scrollToRealTime();
      lastCandleKey = key;
    } else {
      lwSeries.setMarkers(markers);
    }
  }

  async function updateCharts(data) {
    if (chartMode === "tv") {
      ensureTvChart(data.tv_symbol || "UPBIT:BTCKRW", data.tv_interval || "60");
      document.getElementById("chart-meta").textContent = `${data.tv_symbol || "UPBIT:BTCKRW"} · TV`;
    } else {
      await refreshUpbitChart();
    }
  }

  function renderTrades(rows) {
    const ul = document.getElementById("trades");
    const empty = document.getElementById("trades-empty");
    ul.innerHTML = "";
    if (!rows || !rows.length) {
      empty.classList.remove("hidden");
      return;
    }
    empty.classList.add("hidden");
    for (const t of rows.slice().reverse()) {
      const li = document.createElement("li");
      const side = String(t.side || "").toLowerCase();
      const sideEl = document.createElement("span");
      sideEl.className = side === "buy" ? "side-buy" : "side-sell";
      sideEl.textContent = side === "buy" ? "매수" : "매도";
      const mid = document.createElement("span");
      mid.textContent = `${money(t.price)} · ${qty(t.qty)}`;
      const ts = document.createElement("span");
      ts.className = "muted";
      ts.textContent = String(t.ts || "").replace("T", " ").slice(0, 19);
      li.append(sideEl, mid, ts);
      ul.appendChild(li);
    }
  }

  async function refresh() {
    const base = window.__DESK_BASE__ || "/";
    let res;
    try {
      res = await fetch(base + "api/status", { credentials: "same-origin" });
    } catch (e) {
      throw new Error("상태 API 네트워크 오류");
    }
    if (res.status === 401) {
      location.href = base;
      return;
    }
    if (!res.ok) throw new Error(`상태 API ${res.status}`);
    const data = await res.json();
    lastStatus = data;
    const s = data.status || {};
    const risk = s.risk || {};

    const modeEl = document.getElementById("m-mode");
    modeEl.textContent = s.mode === "LIVE" ? "실주문" : s.mode === "PAPER" ? "모의" : s.mode || "—";
    modeEl.className = "pill" + (s.mode === "LIVE" ? " live" : "");

    const regimeEl = document.getElementById("m-regime");
    const regime = data.regime || null;
    if (regime && regime.code) {
      const adx =
        regime.adx != null && !Number.isNaN(Number(regime.adx))
          ? ` · ADX ${Number(regime.adx).toFixed(0)}`
          : "";
      regimeEl.textContent = `${regime.label || regime.code}${adx}`;
      regimeEl.className = `v ${REGIME_CLASS[regime.code] || ""}`.trim();
      regimeEl.title = [
        regime.date ? `일자 ${regime.date}` : null,
        regime.selected_file ? `매핑 ${regime.selected_file}` : null,
        regime.engine ? `engine ${regime.engine}` : null,
      ]
        .filter(Boolean)
        .join(" · ");
    } else {
      regimeEl.textContent = "—";
      regimeEl.className = "v";
      regimeEl.title = "";
    }

    const sig = SIGNAL_KO[s.signal] || s.signal || "—";
    document.getElementById("m-signal").textContent = sig;
    document.getElementById("m-krw").textContent = money(s.krw);
    if (s.position && s.position.qty) {
      document.getElementById("m-pos").textContent = `${qty(s.position.qty)} @ ${money(
        s.position.entry_price
      )}`;
    } else {
      document.getElementById("m-pos").textContent = "없음";
    }
    document.getElementById("m-strategy").textContent = s.strategy || s.strategy_file || "—";

    const riskEl = document.getElementById("m-risk");
    if (risk.trading_halted) {
      riskEl.textContent = risk.halt_buys_only ? "매수중단" : "전면중단";
      riskEl.className = "v warn";
    } else {
      riskEl.textContent = "정상";
      riskEl.className = "v ok";
    }

    if (data.stale) {
      setFreshness("stale", "상태 오래됨");
    } else {
      const t = s.updated_at || (data.mtime ? new Date(data.mtime * 1000).toLocaleString("ko-KR") : "");
      setFreshness("ok", t || "최신");
    }

    document.getElementById("latest-text").textContent = data.latest_text || "(상태 텍스트 없음)";
    renderTrades(data.recent_trades || []);

    try {
      await updateCharts(data);
    } catch (chartErr) {
      console.warn(chartErr);
      setFreshness("stale", `차트: ${chartErr.message || chartErr}`);
    }
  }

  async function loop() {
    try {
      await refresh();
    } catch (e) {
      console.error(e);
      setFreshness("error", `갱신 실패 · ${e.message || e}`);
    }
    setTimeout(loop, 20000);
  }

  document.getElementById("btn-upbit").addEventListener("click", () => setChartMode("upbit"));
  document.getElementById("btn-tv").addEventListener("click", () => {
    destroyUpbitChart();
    setChartMode("tv");
  });

  syncToggleUi();
  loop();
})();
