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

  function money(v, quote) {
    if (v == null || Number.isNaN(Number(v))) return "—";
    const q = String(quote || "KRW").toUpperCase();
    const n = Number(v);
    if (q === "KRW") {
      return `${Math.round(n).toLocaleString("ko-KR")}원`;
    }
    const body = n.toLocaleString("en-US", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    });
    return `${body} ${q}`;
  }

  function shortName(file) {
    if (!file) return "—";
    return String(file)
      .replace(/^.*\//, "")
      .replace(/\.json$/i, "");
  }

  function setText(id, text, className) {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = text;
    if (className != null) el.className = className;
  }

  function renderSleeves(data) {
    const root = document.getElementById("sleeves-panel");
    if (!root) return;
    const sleeves = data.sleeves || {};
    const core = sleeves.core || {};
    const scalp = sleeves.scalp || {};
    const regime = data.regime || {};
    const sw = data.switch || {};
    const bg = data.bitget || {};
    const scalpLive = Boolean(bg.running) && !String(scalp.status || "").includes("cash");

    const rows = [
      {
        tag: "CORE",
        label: core.label || "장타",
        status: core.status_label || core.status || "—",
        ok: String(core.status || "").includes("live"),
        meta: [
          core.venue || "upbit",
          shortName(core.strategy || regime.selected_file || data.status?.strategy),
        ]
          .filter(Boolean)
          .join(" · "),
        note: core.notes || null,
      },
      {
        tag: "SCALP",
        label: scalp.label || "단타",
        status: scalpLive
          ? `가동 · ${shortName(bg.strategy) || "—"}`
          : scalp.status_label || scalp.status || "중지 · cash",
        ok: scalpLive,
        meta: [scalp.venue || "bitget", bg.cash != null ? money(bg.cash, "USDT") : "USDT —"]
          .filter(Boolean)
          .join(" · "),
        note: scalp.notes || null,
      },
    ];

    root.innerHTML = "";
    for (const row of rows) {
      const card = document.createElement("div");
      card.className = "sleeve-card" + (row.ok ? " on" : " off");
      const head = document.createElement("div");
      head.className = "sleeve-head";
      const tag = document.createElement("span");
      tag.className = "sleeve-tag";
      tag.textContent = row.tag;
      const st = document.createElement("span");
      st.className = "sleeve-status";
      st.textContent = row.status;
      head.append(tag, st);
      const title = document.createElement("div");
      title.className = "sleeve-title";
      title.textContent = row.label;
      const meta = document.createElement("div");
      meta.className = "sleeve-meta";
      meta.textContent = row.meta;
      card.append(head, title, meta);
      if (row.note) {
        const note = document.createElement("div");
        note.className = "sleeve-note";
        note.textContent = row.note;
        card.append(note);
      }
      root.appendChild(card);
    }

    const swCard = document.createElement("div");
    swCard.className = "switch-card";
    const swHead = document.createElement("div");
    swHead.className = "sleeve-head";
    const swTag = document.createElement("span");
    swTag.className = "sleeve-tag";
    swTag.textContent = "SWITCH";
    const swSt = document.createElement("span");
    swSt.className =
      "sleeve-status" +
      (sw.action === "position_skip" || sw.action === "dwell_block" ? " warn" : "");
    swSt.textContent = sw.action_label || sw.action || regime.action_label || "—";
    swHead.append(swTag, swSt);
    const swMeta = document.createElement("div");
    swMeta.className = "sleeve-meta";
    const parts = [
      regime.policy ? `Policy ${String(regime.policy).replace(/^C_.*/, "C")}` : null,
      regime.engine ? `engine ${regime.engine}` : null,
      sw.from && sw.to ? `${shortName(sw.from)} → ${shortName(sw.to)}` : shortName(regime.selected_file),
      sw.ts ? String(sw.ts).replace("T", " ").slice(0, 19) : regime.date || null,
    ].filter(Boolean);
    swMeta.textContent = parts.join(" · ") || "스위치 로그 없음";
    swCard.append(swHead, swMeta);
    if (sw.reason) {
      const note = document.createElement("div");
      note.className = "sleeve-note";
      note.textContent = String(sw.reason);
      swCard.append(note);
    }
    root.appendChild(swCard);
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

  function renderSwitchHistory(rows) {
    const ul = document.getElementById("switch-hist");
    const empty = document.getElementById("switch-hist-empty");
    if (!ul || !empty) return;
    ul.innerHTML = "";
    if (!rows || !rows.length) {
      empty.classList.remove("hidden");
      return;
    }
    empty.classList.add("hidden");
    for (const r of rows) {
      const li = document.createElement("li");
      const action = String(r.action || "");
      li.className =
        action === "switched"
          ? "sw-switched"
          : action === "position_skip" || action === "dwell_block"
            ? "sw-skip"
            : "";

      const top = document.createElement("div");
      top.className = "sw-top";
      const act = document.createElement("span");
      act.className = "sw-action";
      act.textContent = r.action_label || action || "—";
      const when = document.createElement("span");
      when.className = "muted";
      when.textContent = String(r.ts || "").replace("T", " ").replace("Z", "").slice(0, 19);
      top.append(act, when);

      const mid = document.createElement("div");
      mid.className = "sw-mid";
      const regimeBit = r.regime_label || r.regime || "—";
      const adx =
        r.adx != null && !Number.isNaN(Number(r.adx)) ? ` ADX ${Number(r.adx).toFixed(0)}` : "";
      const from = shortName(r.from);
      const to = shortName(r.to);
      const arrow = from && to && from !== to ? `${from} → ${to}` : to !== "—" ? to : from;
      mid.textContent = `${regimeBit}${adx}${arrow && arrow !== "—" ? ` · ${arrow}` : ""}`;

      li.append(top, mid);
      if (r.reason) {
        const note = document.createElement("div");
        note.className = "sleeve-note";
        note.textContent = String(r.reason);
        li.append(note);
      }
      ul.appendChild(li);
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
        regime.policy ? `policy ${regime.policy}` : null,
      ]
        .filter(Boolean)
        .join(" · ");
    } else {
      regimeEl.textContent = "—";
      regimeEl.className = "v";
      regimeEl.title = "";
    }

    const sleeves = data.sleeves || {};
    const core = sleeves.core || {};
    const scalp = sleeves.scalp || {};
    const sw = data.switch || {};
    const bg = data.bitget || {};

    setText(
      "m-core",
      shortName(core.strategy || regime?.selected_file || s.strategy || s.strategy_file),
      "v"
    );
    const scalpCash = String(scalp.status || "").includes("cash") || !bg.running;
    setText(
      "m-scalp",
      scalpCash ? scalp.status_label || "중지 · cash" : shortName(bg.strategy) || "가동",
      scalpCash ? "v muted-v" : "v ok"
    );
    const switchLabel = sw.action_label || regime?.action_label || "—";
    const switchWarn = sw.action === "position_skip" || sw.action === "dwell_block";
    setText("m-switch", switchLabel, switchWarn ? "v warn" : "v");

    const sig = SIGNAL_KO[s.signal] || s.signal || "—";
    document.getElementById("m-signal").textContent = sig;
    document.getElementById("m-krw").textContent = money(s.krw ?? s.cash);
    if (s.position && s.position.qty) {
      document.getElementById("m-pos").textContent = `${qty(s.position.qty)} @ ${money(
        s.position.entry_price
      )}`;
    } else {
      document.getElementById("m-pos").textContent = "없음";
    }
    document.getElementById("m-bitget").textContent =
      bg.cash != null ? money(bg.cash, "USDT") : scalpCash ? "cash" : "—";

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
    document.getElementById("bg-latest-text").textContent =
      bg.latest_text || (scalpCash ? "(SCALP 중지 · Bitget 로그 없음)" : "(상태 텍스트 없음)");
    renderSleeves(data);
    renderSwitchHistory(data.switch_history || []);
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
