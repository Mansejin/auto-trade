# Bitget BTC 5m RSI + Ichimoku long/short v1 (research)

## Intent
Regime-agnostic scalp pair for Bitget BTCUSDT-M style research.
Upbit toolkit cannot `exchange=bitget` / true shorts — files are `kr` KRW-BTC sims.
Short file is an **entry-timing proxy** (buys on RSI fade from overbought); short PF is
`invert(trade pnl_pct)` then wins/|losses|.

## Frozen rules

| Side | Entry | Exit | SL / TP |
|---|---|---|---|
| Long | RSI(14) rebound across 22 (prev&lt;22 → now&gt;22) | close below both cloud spans (Leading1/2 offset 26) | 0.5% / 2.0% |
| Short (Bitget) | RSI(14) fade across 68 (prev&gt;68 → now&lt;68) | close above both cloud spans (cover) | 0.3% / 0.8% |

Cloud filter on **entry** was largely dead (n≈0–2); keep Ichimoku on **exit** only.

## Search window (toolkit)
- Period: `2025-08-04` → `2026-08-04` (~1y 5m, ~105k bars)
- fee_rate: `0.0006` (Bitget taker-ish)
- Target: `profit_factor >= 1.2` and `trades >= 20`
- Grid: 240 primary + 160 long-extra → hits found both sides

## Toolkit metrics (quote CSV / search)

| Side | Slug kept | trades | PF used |
|---|---|---|---|
| Long | `bitget-btc-5m-rsi-ichi-long-v1` (= r22 / SL0.5 / TP2.0 / c0-e1) | 364 | **1.517** (toolkit `profit_factor_before_fees`) |
| Short proxy | `bitget-btc-5m-rsi-ichi-short-proxy-v1` (= r68 / SL0.3 / TP0.8 / c0-e1) | 1617 | **1.368** (inverted pnl_pct PF) |

Artifacts: `reports/rsi-ichi-pf-search-20260805/`, `scripts/_search_rsi_ichi_pf12.py`.

## Caveats
- Short proxy Total Return is **not** Bitget short PnL; only inverted trade PF is interpreted for the short sleeve.
- In-sample search over a large grid; user waived overfit concern for this pass — still not a LIVE promotion signal.
- Do not mount to Policy C / CORE from this alone.

## Three-check follow-up (2026-08-05)

| Check | Result |
|---|---|
| (1) OOS halves (toolkit) | Long PF≥1.2 on h1+h2. Short proxy **h1 PF 1.19** (misses 1.2). |
| (2) Freqtrade true short | **Falsified** — PF 0.14–0.24, 19–52 trades. Proxy≠true short. |
| (3) Long R:R fixed 0.5/1.0 | RSI22 + **cloud exit** still PF≥1.2 both halves; SL/TP-only or RSI≥25 falls under 1.2. |

Detail: `reports/rsi-ichi-checks-20260805/SUMMARY.json`.
FT strategies: `RsiIchiScalpLongV1.py`, `RsiIchiScalpShortV1.py`.
