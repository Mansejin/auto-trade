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

  let tvWidget = null;
  let lastTvKey = "";

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

  function showChartError(msg) {
    const el = document.getElementById("chart-error");
    if (!msg) {
      el.classList.add("hidden");
      el.textContent = "";
      return;
    }
    el.textContent = msg;
    el.classList.remove("hidden");
  }

  function waitFrame() {
    return new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
  }

  function hostHeight(el) {
    return Math.max(el.clientHeight || 0, el.offsetHeight || 0, 420);
  }

  function ensureTvChart(symbol, interval) {
    if (typeof TradingView === "undefined" || !TradingView.widget) {
      throw new Error("TradingView 스크립트를 불러오지 못했습니다. 광고차단/네트워크를 확인하세요.");
    }
    const el = document.getElementById("tv_chart");
    if (!el) return;
    const key = `${symbol}|${interval}`;
    if (key === lastTvKey && el.querySelector("iframe")) return;

    lastTvKey = key;
    el.innerHTML = "";
    tvWidget = new TradingView.widget({
      width: "100%",
      height: hostHeight(el),
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
    const s = data.status || {};
    const risk = s.risk || {};

    const modeEl = document.getElementById("m-mode");
    modeEl.textContent = s.mode === "LIVE" ? "실주문" : s.mode === "PAPER" ? "모의" : s.mode || "—";
    modeEl.className = "pill" + (s.mode === "LIVE" ? " live" : "");

    document.getElementById("m-signal").textContent = SIGNAL_KO[s.signal] || s.signal || "—";
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

    const symbol = data.tv_symbol || "UPBIT:BTCKRW";

    try {
      showChartError("");
      await waitFrame();
      ensureTvChart(symbol, data.tv_interval || "60");
    } catch (chartErr) {
      console.warn(chartErr);
      showChartError(String(chartErr.message || chartErr));
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

  loop();
})();
