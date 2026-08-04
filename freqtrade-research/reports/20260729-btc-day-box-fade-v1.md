# BTC Day-Box Fade V1 — 2026-07-29

Card: [`docs/research/btc-day-box-fade-card-frozen.md`](../../docs/research/btc-day-box-fade-card-frozen.md)

Hypothesis: When BTC’s ~1d box is 1–2% wide and ADX soft, fading edges to mid at 5x has edge.

## Spec

| Item | Value |
|------|-------|
| Pair | BTC USDT-perp |
| Strategy | `BtcDayBoxFadeV1` |
| TF | 15m · lookback 96 (~1d) |
| Hypers | `touch_frac=0.15` · `adx_max=25` · `sl_buf_frac=0.05` |
| Lev | 5 |
| Exit | box mid · SL beyond box |

## Results (~30d)

| Window | Trades | Profit % | PF | box_mid / SL | Verdict |
|--------|--------|----------|-----|--------------|---------|
| 2026-05 | 32 | **−16.88%** | 0.52 | 7 / 25 | **fail** |
| 2026-06 | 15 | **−20.21%** | 0.07 | 1 / 14 | **fail** |
| 2026-07 | 22 | **−12.08%** | 0.57 | 5 / 17 | **fail** |

**Falsified** (3/3). Stops dominate; mid hits too rare vs edge false breaks.

## Read

- Idea family (S/R box fade) still matches ask — **this rolling Donchian-style box** is a weak proxy for a “held day box”.
- **Do not retune** hypers.
- Revision candidates (new cards): fixed swing box (not rolling every bar), require 2+ touches before fade, enter only on rejection wick at edge, pause on range *expansion* rate, divergence/event card later.
- LIVE: **no**. Nassi line stays parked.
