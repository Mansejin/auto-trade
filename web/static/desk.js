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

  let tvWidget = null;
  let lastTvKey = "";
  let lastStatus = null;
  let tvBooted = false;

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

  function shortName(file, maxLen) {
    if (!file) return "—";
    let s = String(file)
      .replace(/^.*\//, "")
      .replace(/\.json$/i, "");
    const max = maxLen == null ? 20 : maxLen;
    if (s.length > max) s = s.slice(0, Math.max(1, max - 1)) + "…";
    return s;
  }

  function setText(id, text, className, title) {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = text;
    if (className != null) el.className = className;
    if (title != null) el.title = title;
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

  function renderStatusBlock(elId, text) {
    const root = document.getElementById(elId);
    if (!root) return;
    root.innerHTML = "";
    const raw = String(text || "").trim();
    if (!raw) {
      root.innerHTML = '<p class="muted empty">상태 텍스트 없음</p>';
      return;
    }
    const lines = raw.split(/\r?\n/);
    let dl = null;
    let pairs = 0;
    const flush = () => {
      if (dl && pairs) root.appendChild(dl);
      dl = null;
      pairs = 0;
    };
    const skipKeys = new Set(["시각", "모드"]);
    for (const line of lines) {
      const t = line.trim();
      if (!t) continue;
      if (/^[=\-]{3,}/.test(t) || /^----/.test(t)) {
        flush();
        const label = t.replace(/^[=\-\s]+|[=\-\s]+$/g, "").trim();
        if (label && label !== "봇 상태") {
          const h = document.createElement("div");
          h.className = "status-section";
          h.textContent = label;
          root.appendChild(h);
        }
        continue;
      }
      const m = t.match(/^([^:：]{1,24})\s*[:：]\s*(.+)$/);
      if (!m) continue;
      const key = m[1].trim();
      if (skipKeys.has(key)) continue;
      if (!dl) {
        dl = document.createElement("dl");
        dl.className = "status-kv";
      }
      const dt = document.createElement("dt");
      dt.textContent = key;
      const dd = document.createElement("dd");
      dd.textContent = m[2].trim();
      dl.append(dt, dd);
      pairs += 1;
    }
    flush();
    if (!root.childElementCount) {
      const pre = document.createElement("pre");
      pre.className = "status-pre";
      pre.textContent = raw;
      root.appendChild(pre);
    }
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

  function loadTradingView(onReady) {
    if (typeof TradingView !== "undefined" && TradingView.widget) {
      onReady();
      return;
    }
    const existing = document.querySelector('script[data-desk-tv="1"]');
    if (existing) {
      existing.addEventListener("load", onReady);
      return;
    }
    const s = document.createElement("script");
    s.src = "https://s3.tradingview.com/tv.js";
    s.async = true;
    s.dataset.deskTv = "1";
    s.onload = onReady;
    s.onerror = () => {
      setFreshness("stale", "차트 CDN 차단/실패");
    };
    document.head.appendChild(s);
  }

  function ensureTvChart(symbol, interval) {
    loadTradingView(() => {
      if (typeof TradingView === "undefined" || !TradingView.widget) {
        return;
      }
      const key = `${symbol}|${interval}`;
      if (key === lastTvKey && tvWidget) return;
      lastTvKey = key;
      const el = document.getElementById("tv_chart");
      if (!el) return;
      el.innerHTML = "";
      try {
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
        tvBooted = true;
      } catch (e) {
        console.warn(e);
        setFreshness("stale", `차트: ${e.message || e}`);
      }
    });
  }

  function updateCharts(data) {
    const symbol = data.tv_symbol || "UPBIT:BTCKRW";
    const interval = data.tv_interval || "60";
    ensureTvChart(symbol, interval);
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

  function renderTrades(rows, quote, ulId, emptyId) {
    const ul = document.getElementById(ulId || "trades");
    const empty = document.getElementById(emptyId || "trades-empty");
    if (!ul || !empty) return;
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

    const coreFull = core.strategy || regime?.selected_file || s.strategy || s.strategy_file || "";
    setText(
      "m-core",
      shortName(coreFull),
      "v",
      String(coreFull).replace(/^.*\//, "").replace(/\.json$/i, "") || undefined
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
    const switchEl = document.getElementById("m-switch");
    if (switchEl) {
      switchEl.title = [sw.reason, sw.from && sw.to ? `${shortName(sw.from)} → ${shortName(sw.to)}` : null, sw.ts]
        .filter(Boolean)
        .join(" · ");
    }

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
    const bgSig = document.getElementById("m-bg-signal");
    if (bgSig) bgSig.textContent = SIGNAL_KO[bg.signal] || bg.signal || (scalpCash ? "중지" : "—");
    const bgPos = document.getElementById("m-bg-pos");
    if (bgPos) {
      if (bg.position && bg.position.qty) {
        bgPos.textContent = `${qty(bg.position.qty)} @ ${money(bg.position.entry_price, "USDT")}`;
      } else {
        bgPos.textContent = scalpCash ? "—" : "없음";
      }
    }

    const xfer = data.transfer || null;
    const xferEl = document.getElementById("m-xfer");
    const xferTick = document.getElementById("tick-xfer");
    if (xferEl) {
      if (xfer && xfer.code) {
        xferEl.textContent = String(xfer.code);
        xferEl.className = "v warn";
        xferEl.title = [
          xfer.direction,
          xfer.coin && xfer.amount != null ? `${xfer.coin} ${xfer.amount}` : null,
          xfer.detail,
          xfer.created_at,
        ]
          .filter(Boolean)
          .join(" · ");
        if (xferTick) xferTick.classList.add("tick-pri");
      } else {
        xferEl.textContent = "없음";
        xferEl.className = "v muted-v";
        xferEl.title = "";
        if (xferTick) xferTick.classList.remove("tick-pri");
      }
    }

    const riskEl = document.getElementById("m-risk");
    if (risk.trading_halted) {
      const why = String(risk.halt_reason || "").trim();
      riskEl.textContent = risk.halt_buys_only ? "매수중단" : "전면중단";
      if (why && why.length <= 18) riskEl.textContent += ` · ${why}`;
      riskEl.className = "v warn";
      riskEl.title = [
        why || null,
        risk.consecutive_errors != null ? `연속오류 ${risk.consecutive_errors}` : null,
        risk.day_start_equity != null ? `일초 자산 ${Math.round(Number(risk.day_start_equity)).toLocaleString("ko-KR")}` : null,
      ]
        .filter(Boolean)
        .join(" · ");
    } else {
      riskEl.textContent = "정상";
      riskEl.className = "v ok";
      riskEl.title =
        risk.day_start_equity != null
          ? `일초 자산 ${Math.round(Number(risk.day_start_equity)).toLocaleString("ko-KR")}`
          : "";
    }

    if (data.stale) {
      setFreshness("stale", "상태 오래됨");
    } else {
      const t = s.updated_at || (data.mtime ? new Date(data.mtime * 1000).toLocaleString("ko-KR") : "");
      setFreshness("ok", t || "최신");
    }

    renderStatusBlock("latest-status", data.latest_text || "");
    renderStatusBlock(
      "bg-latest-status",
      bg.latest_text || (scalpCash ? "모드: SCALP 중지 · cash" : "")
    );
    renderSleeves(data);
    renderSwitchHistory(data.switch_history || []);
    renderTrades(data.recent_trades || [], "KRW", "trades", "trades-empty");
    renderTrades(bg.recent_trades || [], "USDT", "bg-trades", "bg-trades-empty");
    // Chart is sync and must not block/lock status refresh if TV script is slow.
    updateCharts(data);
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

  const tickerMore = document.getElementById("btn-ticker-more");
  const tickerStrip = document.querySelector(".ticker-strip");
  if (tickerMore && tickerStrip) {
    tickerMore.addEventListener("click", () => {
      const open = tickerStrip.classList.toggle("expanded");
      tickerMore.setAttribute("aria-expanded", open ? "true" : "false");
      tickerMore.textContent = open ? "접기" : "더보기";
    });
  }

  loop();
})();
