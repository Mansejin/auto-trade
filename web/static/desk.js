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
  let lastOkAt = null;
  let lastFreshKind = "stale";
  let lastFreshFallback = "갱신 대기";
  let refreshBusy = false;

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

  function relativeAge(ts) {
    if (!ts) return null;
    const sec = Math.max(0, Math.round((Date.now() - ts) / 1000));
    if (sec < 5) return "방금";
    if (sec < 60) return `${sec}초 전`;
    const min = Math.floor(sec / 60);
    if (min < 60) return `${min}분 전`;
    const hr = Math.floor(min / 60);
    if (hr < 48) return `${hr}시간 전`;
    return `${Math.floor(hr / 24)}일 전`;
  }

  function setFreshness(kind, text) {
    lastFreshKind = kind;
    if (kind === "ok") {
      lastOkAt = Date.now();
      lastFreshFallback = text || "최신";
    } else {
      lastFreshFallback = text || lastFreshFallback;
    }
    paintFreshness();
  }

  function paintFreshness() {
    const pulse = document.getElementById("pulse");
    const label = document.getElementById("fresh-text");
    let text = lastFreshFallback;
    if (lastFreshKind === "ok" && lastOkAt) {
      const age = relativeAge(lastOkAt);
      text = age ? `${age}` : lastFreshFallback;
    }
    if (label) label.textContent = text;
    if (pulse) {
      pulse.classList.toggle("stale", lastFreshKind === "stale" || lastFreshKind === "error");
      pulse.classList.toggle("ok", lastFreshKind === "ok");
    }
  }

  function showChartError(msg) {
    const el = document.getElementById("chart-error");
    if (!el) return;
    if (!msg) {
      el.classList.add("hidden");
      el.textContent = "";
      return;
    }
    el.textContent = msg;
    el.classList.remove("hidden");
  }

  function renderRegimeStrip(data) {
    const root = document.getElementById("regime-strip");
    if (!root) return;
    const regime = data.regime || {};
    if (!regime.code) {
      root.textContent = "";
      root.className = "regime-strip";
      return;
    }
    const adx =
      regime.adx != null && !Number.isNaN(Number(regime.adx))
        ? ` · ADX ${Number(regime.adx).toFixed(0)}`
        : "";
    root.className = `regime-strip ${REGIME_CLASS[regime.code] || ""}`.trim();
    root.innerHTML = "";
    const title = document.createElement("span");
    title.textContent = `${regime.label || regime.code}${adx}`;
    root.appendChild(title);
    const metaBits = [
      regime.date ? `일자 ${regime.date}` : null,
      regime.selected_file ? shortName(regime.selected_file, 28) : null,
      regime.policy ? `policy ${String(regime.policy).replace(/^C_.*/, "C")}` : null,
    ].filter(Boolean);
    if (metaBits.length) {
      const meta = document.createElement("span");
      meta.className = "regime-meta";
      meta.textContent = metaBits.join(" · ");
      root.appendChild(meta);
    }
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
        tag: "CORE · 장타",
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
        tag: "SCALP · 단타",
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
    swTag.textContent = "SWITCH · 전환";
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

  function renderStatusBlock(elId, text, opts) {
    const root = document.getElementById(elId);
    if (!root) return;
    root.innerHTML = "";
    const raw = String(text || "").trim();
    if (!raw) {
      root.innerHTML = '<p class="muted empty">상태 텍스트 없음</p>';
      return;
    }
    const hideIndicators = Boolean(opts && opts.hideIndicators);
    const lines = raw.split(/\r?\n/);
    let dl = null;
    let pairs = 0;
    let skipPairs = false;
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
        skipPairs = hideIndicators && label === "주요 지표";
        if (label && label !== "봇 상태" && !skipPairs) {
          const h = document.createElement("div");
          h.className = "status-section";
          h.textContent = label;
          root.appendChild(h);
        }
        continue;
      }
      if (skipPairs) continue;
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

  function fmtMeterNum(v) {
    const n = Number(v);
    if (!Number.isFinite(n)) return "—";
    if (Math.abs(n) >= 1000) return Math.round(n).toLocaleString("ko-KR");
    return String(Math.round(n * 100) / 100);
  }

  function renderMeters(elId, meters) {
    const root = document.getElementById(elId);
    if (!root) return;
    root.innerHTML = "";
    if (!meters || !meters.length) {
      root.hidden = true;
      return;
    }
    root.hidden = false;
    const head = document.createElement("div");
    head.className = "meters-head";
    head.textContent = "조건 대비";
    root.appendChild(head);
    for (const m of meters) {
      const row = document.createElement("div");
      const metClass = m.met === true ? "met" : m.met === false ? "unmet" : "unk";
      row.className = `meter ${metClass}`;

      const top = document.createElement("div");
      top.className = "meter-top";
      const title = document.createElement("span");
      title.className = "meter-title";
      title.textContent = `${m.side_label || ""} ${m.label || ""}`.trim();
      const rule = document.createElement("span");
      rule.className = "meter-rule";
      if (m.kind === "compare") {
        rule.textContent = `${fmtMeterNum(m.left)} ${m.op_sym || ""} ${fmtMeterNum(m.right)}`;
      } else {
        rule.textContent = `${fmtMeterNum(m.value)} ${m.op_sym || ""} ${fmtMeterNum(m.threshold)}`;
      }
      const badge = document.createElement("span");
      badge.className = "meter-badge";
      badge.textContent = m.met === true ? "충족" : m.met === false ? "미충족" : "—";
      top.append(title, rule, badge);

      const track = document.createElement("div");
      track.className = "meter-track";
      const lo = Number(m.min);
      const hi = Number(m.max);
      const span = hi - lo || 1;
      const clampPct = (x) => Math.max(0, Math.min(100, ((Number(x) - lo) / span) * 100));
      const fill = document.createElement("div");
      fill.className = "meter-fill";
      fill.style.width = `${clampPct(m.kind === "compare" ? m.left : m.value)}%`;
      const mark = document.createElement("div");
      mark.className = "meter-mark";
      mark.style.left = `${clampPct(m.kind === "compare" ? m.right : m.threshold)}%`;
      mark.title = m.kind === "compare" ? String(m.right_label || "기준") : `임계 ${fmtMeterNum(m.threshold)}`;
      track.append(fill, mark);

      row.append(top, track);
      root.appendChild(row);
    }
  }

  function qty(v) {
    if (v == null || Number.isNaN(Number(v))) return "—";
    return Number(v)
      .toFixed(8)
      .replace(/\.?0+$/, "");
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
      showChartError("차트 CDN 차단/실패 — 상태·체결은 정상 갱신됩니다.");
      setFreshness("stale", "차트 CDN 실패");
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
      showChartError("");
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
      } catch (e) {
        console.warn(e);
        showChartError(`차트: ${e.message || e}`);
        setFreshness("stale", `차트: ${e.message || e}`);
      }
    });
  }

  function updateCharts(data) {
    const symbol = data.tv_symbol || "UPBIT:BTCKRW";
    const interval = data.tv_interval || "60";
    const meta = document.getElementById("chart-meta");
    if (meta) {
      const tf = data.timeframe || interval;
      meta.textContent = `${symbol} · ${tf}`;
    }
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

  function setHaltBanner(risk) {
    const banner = document.getElementById("halt-banner");
    const title = document.getElementById("halt-title");
    const detail = document.getElementById("halt-detail");
    if (!banner || !title || !detail) return;
    if (risk && risk.trading_halted) {
      const why = String(risk.halt_reason || "").trim();
      title.textContent = risk.halt_buys_only ? "매수 중단" : "거래 전면 중단";
      const bits = [
        why || null,
        risk.consecutive_errors != null ? `연속오류 ${risk.consecutive_errors}` : null,
      ].filter(Boolean);
      detail.textContent = bits.join(" · ") || "사유 없음 — risk.json / 텔레그램 확인";
      banner.hidden = false;
      banner.classList.remove("hidden");
    } else {
      banner.hidden = true;
      banner.classList.add("hidden");
      detail.textContent = "";
    }
  }

  async function refresh() {
    if (refreshBusy) return;
    refreshBusy = true;
    const btn = document.getElementById("btn-refresh");
    if (btn) btn.disabled = true;
    const base = window.__DESK_BASE__ || "/";
    try {
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
      if (modeEl) {
        modeEl.textContent = s.mode === "LIVE" ? "실주문" : s.mode === "PAPER" ? "모의" : s.mode || "—";
        modeEl.className = "pill" + (s.mode === "LIVE" ? " live" : "");
      }

      const sleeves = data.sleeves || {};
      const scalp = sleeves.scalp || {};
      const bg = data.bitget || {};
      const scalpCash = String(scalp.status || "").includes("cash") || !bg.running;

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
          const side = bg.position.side ? `${String(bg.position.side).toUpperCase()} ` : "";
          bgPos.textContent = `${side}${qty(bg.position.qty)} @ ${money(bg.position.entry_price, "USDT")}`;
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
          if (xferTick) {
            xferTick.classList.add("tick-pri");
            xferTick.classList.remove("tick-sec");
          }
        } else {
          xferEl.textContent = "없음";
          xferEl.className = "v muted-v";
          xferEl.title = "";
          if (xferTick) {
            xferTick.classList.remove("tick-pri");
            xferTick.classList.add("tick-sec");
          }
        }
      }

      const riskEl = document.getElementById("m-risk");
      if (risk.trading_halted) {
        riskEl.textContent = risk.halt_buys_only ? "매수중단" : "전면중단";
        riskEl.className = "v warn";
        riskEl.title = String(risk.halt_reason || "");
      } else {
        riskEl.textContent = "정상";
        riskEl.className = "v ok";
        riskEl.title =
          risk.day_start_equity != null
            ? `일초 자산 ${Math.round(Number(risk.day_start_equity)).toLocaleString("ko-KR")}`
            : "";
      }
      setHaltBanner(risk);

      if (data.stale) {
        setFreshness("stale", "상태 오래됨");
      } else {
        setFreshness("ok", "최신");
      }

      const ubMeters = data.condition_meters || [];
      const bgMeters = bg.condition_meters || [];
      renderMeters("ub-meters", ubMeters);
      renderMeters("bg-meters", bgMeters);
      renderStatusBlock("latest-status", data.latest_text || "", {
        hideIndicators: ubMeters.length > 0,
      });
      renderStatusBlock(
        "bg-latest-status",
        bg.latest_text || (scalpCash ? "모드: SCALP 중지 · cash" : ""),
        { hideIndicators: bgMeters.length > 0 }
      );
      renderRegimeStrip(data);
      renderSleeves(data);
      renderSwitchHistory(data.switch_history || []);
      renderTrades(data.recent_trades || [], "KRW", "trades", "trades-empty");
      renderTrades(bg.recent_trades || [], "USDT", "bg-trades", "bg-trades-empty");
      updateCharts(data);
    } finally {
      refreshBusy = false;
      if (btn) btn.disabled = false;
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

  function wireTabs() {
    document.querySelectorAll(".seg-tabs .seg").forEach((btn) => {
      btn.addEventListener("click", () => {
        const tab = btn.getAttribute("data-tab");
        const target = btn.getAttribute("data-target");
        if (!tab || !target) return;
        document.querySelectorAll(`.seg-tabs .seg[data-tab="${tab}"]`).forEach((b) => {
          const on = b === btn;
          b.classList.toggle("active", on);
          b.setAttribute("aria-selected", on ? "true" : "false");
        });
        document.querySelectorAll(`.tab-pane[data-pane="${tab}"]`).forEach((pane) => {
          pane.classList.toggle("hidden", pane.getAttribute("data-for") !== target);
        });
      });
    });
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

  const refreshBtn = document.getElementById("btn-refresh");
  if (refreshBtn) {
    refreshBtn.addEventListener("click", () => {
      refresh().catch((e) => {
        console.error(e);
        setFreshness("error", `갱신 실패 · ${e.message || e}`);
      });
    });
  }

  const chartExpand = document.getElementById("btn-chart-expand");
  const chartPlane = document.querySelector(".chart-plane");
  if (chartExpand && chartPlane) {
    chartExpand.addEventListener("click", () => {
      const open = chartPlane.classList.toggle("expanded");
      chartExpand.setAttribute("aria-pressed", open ? "true" : "false");
      chartExpand.textContent = open ? "차트 작게" : "차트 크게";
    });
  }

  wireTabs();
  setInterval(paintFreshness, 5000);
  loop();
})();
