# Hammer Reclaim Long V1 — 2026-07-29

Card: [`docs/research/hammer-reclaim-long-card-frozen.md`](../../docs/research/hammer-reclaim-long-card-frozen.md)

Hypothesis: 15m long lower-wick + green candle longs (SL at wick low) have edge on BTC/ETH/SOL 24h.

## Spec

| Item | Value |
|------|-------|
| Pairs | BTC, ETH, SOL USDT-perp |
| Strategy | `HammerReclaimLongV1` |
| Config | `config.bitget-hammer-reclaim-long.json` |
| Hypers | `wick_body_k=2`, `min_wick_frac=0.55`, `body_max_frac=0.35` (**frozen**) |
| Exit | custom SL @ signal low · ROI 1% |
| Fee | 0.06% |

## Results (~30d, aggregate)

| Window | Trades (avg/day) | Profit % | PF | Market | Verdict |
|--------|------------------|----------|-----|--------|---------|
| 2026-05 | 336 (11.2) | **−19.83%** | 0.35 | −4.9% | **fail** |
| 2026-06 | 306 (10.6) | **−14.54%** | 0.57 | −15.9% | **fail** |
| 2026-07 | 311 (11.1) | **−9.79%** | 0.65 | +7.1% | **fail** |

**Falsified** (3/3). Frequency far above discretionary 되돌림; expectancy negative.

## Read

- Idea family (wick rejection / pullback) still matches preference — **this encoding** is too loose on 15m.
- **Do not retune** the three hypers.
- Card revision candidates (new card, not knobs): **1h/4h hammer only**, or “hammer after N% drop”, or “one trade per day”.
- LIVE/SCALP: **no**.
