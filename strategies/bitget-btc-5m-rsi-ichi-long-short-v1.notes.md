# Bitget BTC 5m RSI + Ichimoku — research notes

## Intent
Regime-agnostic scalp research. Long kept on toolkit KRW-BTC; **short only on Bitget freqtrade** (true futures).

## Long (retained toolkit) — RESEARCH only, not LIVE

| Entry | Exit | SL/TP |
|---|---|---|
| RSI(14) rebound across 22 | close below both cloud spans (offset 26) | 0.5% / 2.0% |

File: `strategies/bitget-btc-5m-rsi-ichi-long-v1.json`

**What looked good:** OOS halves pre-fee PF ~1.46 / 1.53, n~180+.

**Why not LIVE:**
- Reported PF is toolkit `profit_factor_before_fees` (fees not in PF).
- Absolute return still negative in that window (h1 ~−16%, h2 ~−15%) — beat BH (−27%) but lost capital.
- Exits are almost all cloud sells (tiny holds); fees turn many “green” ticks into KRW losses.
- Cloud exit is load-bearing; Bitget FT true-long got **0 fills** (exit already true on signal bars).

Keep as research artifact only — do not promote to Policy C / Bitget LIVE.

## Short — methodology correction

**Deprecated / do not use PF from:** `strategies/bitget-btc-5m-rsi-ichi-short-proxy-v1.json`  
Upbit long-only invert is not a short PnL sim (fills inflated; PF not transferable).

### True-short redesign (freqtrade Bitget BTC/USDT:USDT 5m)
Entry: RSI fade across 68 AND price not fully above cloud; Exit: SL0.3% / TP0.8% only.  
File: `freqtrade-research/user_data/strategies/RsiIchiScalpShortV3.py`

Search (v2–v4, PF≥1.2 & n≥20 on both halves): **no hit**.
- Best non-hit V3: h1 PF 1.10 / n19, h2 PF 0.99 / n32
- Plain RSI fade (no cloud): n large, PF ~0.63–0.67
- Artifact: `reports/rsi-ichi-short-v3-20260805/search-summary.json`

### Pivot: RSI+BB short (also true FT)
`RsiBbScalpShortV5` — RSI>thr + close>BB upper + ADX gate, SL/ROI only.  
54-config OOS search: **no hit**. Best min-half PF ~0.82 (`r70_lt30_sl0.4_tp1.2`).  
Artifact: `reports/rsi-bb-short-v5-20260805/search-summary.json`

Mean-reversion fade shorts struggle on this Bitget window (large BTC drawdown tape).

## Caveats
Backtests omit full live friction; not a LIVE/Policy C promotion signal.
