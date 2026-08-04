# BTC Swing-Box Fade V1 — 2026-07-29

Card: [`docs/research/btc-swing-box-fade-card-frozen.md`](../../docs/research/btc-swing-box-fade-card-frozen.md)

Fixed swing HH/LL box, ≥2 touches/side, rejection entry, wick SL, mid TP, lev 5.

## Results

| Window | Trades | Profit % | PF | mid / SL | Verdict |
|--------|--------|----------|-----|----------|---------|
| 2026-05 | 8 | **−2.97%** | 0.49 | 3 / 5 | **fail** |
| 2026-06 | 13 | **−9.39%** | 0.36 | 4 / 7 | **fail** |
| 2026-07 | 12 | **−1.57%** | 0.84 | 5 / 6 | **fail** |

**Falsified** (3/3).

## vs rolling box line

| | Day-box V2 | Swing-box |
|--|------------|-----------|
| May | −2.95% | −2.97% |
| Jun | −6.04% | −9.39% |
| Jul | −4.15% | −1.57% |

Still SL-heavy. Fixed swings did not create edge on these windows.

## Read

- Do **not** retune.
- Box-fade family on BTC 15m lev5 looks weak under this S/R encoding class.
- LIVE: **no**. Next = new one-liner (not another box gate).
