# Bitget BTC short — swing HIT (keep), scalp closed

## Keep: 5m swing short

| Field | Value |
|-------|--------|
| Entry | `di_cloud`: −DI > +DI, ADX ≥ 15, close below both Ichimoku spans |
| Exit | SL 3% / TP 9%, no trail |
| TF | 5m |
| Fee model | 6 bps/side |
| OOS | h1 `2025-09-01`→`2026-02-04`, h2 `2026-02-04`→`2026-08-05` |

**Freqtrade check (stake=100, `use_order_book=false`):**

| Window | Trades | PF |
|--------|--------|-----|
| h1 | 27 | 1.44 |
| h2 | 33 | 1.20 |

Both halves pass PF ≥ 1.2. Trade count (~30/half ≈ 1 trade / 5–6 days) is **swing**, not ultra-scalp — accepted.

**Files**

- `freqtrade-research/user_data/strategies/TrendShortV1.py`
- `cpp-bt/strategies/trend_short_swing_v1.json`
- Alignment notes: `reports/trend-short-cpp-aligned-20260805/`

## Closed: ultra-short / scalp

RSI fade / BB reject on 5m and 1m: after-fee best minPF ≈ 0.86–0.93.  
Judged bars PF≥1.10@n150 and PF≥1.15@n100: **0 hits**.  
fee=0 theoretical ~1.13 is not bankable under 12 bps RT.  
See `reports/scalp-pf-threshold-20260805/`.

Do not promote scalp grids to LIVE.
