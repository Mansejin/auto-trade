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

  function money(v, quote) {
    if (v == null || Number.isNaN(Number(v))) return "—";
    const q = String(quote || "KRW").toUpperCase();
    const n = Number(v);
    if (q === "KRW") {
      return `${Math.round(n).toLocaleString("ko-KR")}원`;
    }
    const digits = 2;
    const body = n.toLocaleString("en-US", {
      minimumFractionDigits: 0,
      maximumFractionDigits: digits,
    });
    return `${body} ${q}`;
  }

  function cashValue(s) {
    if (s.cash != null) return s.cash;
    if (s.usdt != null) return s.usdt;
    return s.krw;
  }

  function quoteOf(s, data) {
    return (
      s.quote_currency ||
      data.quote_currency ||
      (String(s.exchange || data.exchange || "").toLowerCase() === "bitget"
        ? "USDT"
        : "KRW")
    );
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

  function renderTrades(rows, quote, ulId, emptyId) {
    const ul = document.getElementById(ulId || "trades");
    const empty = document.getElementById(emptyId || "trades-empty");
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
      mid.textContent = `${money(t.price, quote)} · ${qty(t.qty)}`;
      const ts = document.createElement("span");
      ts.className = "muted";
      ts.textContent = String(t.ts || "").replace("T", " ").slice(0, 19);
      li.append(sideEl, mid, ts);
      ul.appendChild(li);
    }
  }

  function deskBase() {
    if (window.__DESK_BASE__) return window.__DESK_BASE__;
    const p = location.pathname || "/";
    return p.indexOf("/autotrade") === 0 ? "/autotrade/" : "/";
  }

  async function refresh() {
    const base = deskBase();
    let res;
    try {
      res = await fetch(base + "api/status", { credentials: "same-origin" });
    } catch (e) {
      throw new Error("상태 API 네트워크 오류");
    }
    if (res.status === 401) {
      location.href = deskBase();
      return;
    }
    if (!res.ok) throw new Error(`상태 API ${res.status}`);
    const data = await res.json();
    const s = data.status || {};
    const risk = s.risk || {};

    const modeEl = document.getElementById("m-mode");
    modeEl.textContent = s.mode === "LIVE" ? "실주문" : s.mode === "PAPER" ? "모의" : s.mode || "—";
    modeEl.className = "pill" + (s.mode === "LIVE" ? " live" : "");

    const quote = quoteOf(s, data);
    const cashLabel = document.getElementById("m-cash-label");
    if (cashLabel) cashLabel.textContent = quote === "KRW" ? "원화" : quote;

    // Upbit
    document.getElementById("m-signal").textContent = SIGNAL_KO[s.signal] || s.signal || "—";
    document.getElementById("m-krw").textContent = money(cashValue(s), quote);
    if (s.position && s.position.qty) {
      document.getElementById("m-pos").textContent = `${qty(s.position.qty)} @ ${money(
        s.position.entry_price,
        quote
      )}`;
    } else {
      document.getElementById("m-pos").textContent = "없음";
    }

    // Bitget
    const bg = data.bitget || {};
    document.getElementById("m-bitget").textContent = bg.cash != null ? money(bg.cash, "USDT") : "—";
    document.getElementById("m-bg-signal").textContent = SIGNAL_KO[bg.signal] || bg.signal || "—";
    if (bg.position && bg.position.qty) {
      document.getElementById("m-bg-pos").textContent = `${qty(bg.position.qty)} @ ${money(
        bg.position.entry_price,
        "USDT"
      )}`;
    } else {
      document.getElementById("m-bg-pos").textContent = "없음";
    }

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
    document.getElementById("bg-latest-text").textContent = bg.latest_text || "(상태 텍스트 없음)";
    renderTrades(data.recent_trades || [], quote, "trades", "trades-empty");
    renderTrades(bg.recent_trades || [], "USDT", "bg-trades", "bg-trades-empty");

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
