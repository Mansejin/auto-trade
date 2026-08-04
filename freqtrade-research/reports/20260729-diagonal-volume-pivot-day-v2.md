# 빗각 V2 day — volume-pivot failed-break retest (BTC 15m) — 2026-07-29

## Spec (frozen)

| Item | Value |
|------|-------|
| Pair | Bitget `BTC/USDT:USDT` only |
| TF | 15m |
| Anchors / channel / liq | **same as V1** (no retune) |
| Mode | **B** — failed rail break → reclaim in trend direction |
| Lookback for fail | prior 3 bars beyond rail |
| Exit | mid / ROI +1% / SL −0.5% |
| Fee | 0.06% taker |
| Code | `DiagonalVolumePivotBreakRetestDayV2.py` (extends V1) |
| Config | `config.bitget-diagonal-day-v2.json` |

Hypothesis: failed-break + reclaim beats V1 first-touch on the same rails.

## Results

| Window | Trades (avg/day) | Profit | PF | Market | vs falsify gate |
|--------|------------------|--------|-----|--------|-----------------|
| W1 05-15→05-29 | 18 (1.29) | −1.16% | 0.66 | −9.5% | fail |
| W2 06-15→06-29 | 7 (0.5) | +0.18% | 1.10 | −9.5% | weak pass |
| W3 07-01→07-15 | 11 (0.79) | +0.41% | 1.16 | +10.7% | weak pass |

**PF gate**: only 1/3 windows fail → **not falsified** by the written ≥2/3 rule.

**Practical verdict**: **do not promote**.

- Day-trade goal was ~3–4/day; V2 does **0.5–1.3/day**.
- W2/W3 wins are tiny with **n=7–11** — noise, not an edge claim.
- Stricter entry vs V1 cut losers and winners; leftover expectancy ≈ fee noise.

## Compare to V1-day

| | V1 Mode A | V2 Mode B |
|--|-----------|-----------|
| W1 PF | 1.06 | 0.66 |
| W2 PF | 0.79 | 1.10 |
| W3 PF | 0.60 | 1.16 |
| Trades/day | 1.5–2.6 | 0.5–1.3 |
| Gate | falsified | survives (weak) |

## Do not

- Retune `fail_lookback` / V1 hypers after these numbers.
- Fund SCALP / LIVE on this.

## Next (pick)

1. **Longer OOS** (e.g. 3× 30d) before calling V2 alive — still research.
2. **V1-gate** (direction filter on denser Mode A) if frequency matters more.
3. **Alert-only** — closest to discretionary 빗각; bot draws rails + pings reclaim.
