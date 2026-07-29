# Bear short scalp research — 2026-07-29

Venue: Bitget `BTC/USDT:USDT` isolated futures via Freqtrade (`fee=0.06%` taker).
Upbit spot bot cannot short — Policy C bear (`m5-v6`) **unchanged**.

Windows (daily-bear calendar): `20251117-20251228`, `20260121-20260304`, `20260528-20260714`.

Falsify if ≥2/3 windows: PF&lt;1 or return&lt;0 or WR&lt;38%, or any window MDD&gt;10%.

## Results

| Ver | Idea | W1 | W2 | W3 | Verdict |
|---|---|---|---|---|---|
| v1 `BearShortScalpRsiBbV1` | 5m RSI&gt;70 + BB upper + ADX + −DI | 0 trades | — | — | structure dead (no samples) |
| v2 `BearShortMomentumV2` | 5m RSI×50 below EMA20 | 56 / PF0.71 / −3.1% | 59 / 0.78 / −2.6% | 81 / 0.24 / −12.6% | **falsified** |
| v3 `BearShortRallyFadeV3` | 15m RSI&gt;58 above EMA + −DI | 4 / PF10.8 / +0.8% | 1 / +0.07% | 1 / −0.61% | inconclusive (n too small) |
| v4 `BearShortHtfFadeV4` | 1h EMA50&lt;200 + RSI&gt;65 level | 127 / 0.38 / −19.6% | 203 / 0.65 / −18.8% | 136 / 0.81 / −5.7% | **falsified** (continuous re-entry) |
| v5 `BearShortHtfFadeV5` | same HTF + RSI crossed_above 65 | 82 / 0.43 / −9.2% | 126 / 0.56 / −13.8% | 98 / 0.75 / −5.0% | **falsified** |
| v6 `BearShortBreakdownVolV6` | 15m BB lower cross + vol≥1.5×SMA + ADX≥25 + 1h bear | 18 / 0.86 / −1.0% | 36 / 0.68 / −5.2% | 26 / 1.10 / +1.1% | **falsified** (2/3 fail) |

## Takeaways

1. Fee-aware 5m short scalps without a strong edge lose to 0.12% round-trip + noise.
2. “Short weakness” (v2) and “short pop start” (v5) both lose in calendar-bear windows — pops often continue enough to hit SL/exit before ROI.
3. 15m rally-fade (v3) is the only non-negative sketch, but 1–4 trades/window is not enough to promote.
4. Do **not** mount any of these on LIVE bear map.

## Files

- Strategies: `freqtrade-research/user_data/strategies/BearShort*.py`
- Configs: `config.bitget-bear-short.json`, `-v3.json`, `-v4.json`, `-v5.json`

## Allocation note (2026-07-29)

Bear short work is **SCALP sleeve only** — does not replace CORE `m5-v6`.
See `config/sleeves.json` and `docs/dual-sleeve-allocation.md`.

## Next (needs new frozen hypothesis, not threshold retune)

- Different bear-scalp structure (e.g. funding + breakdown, or 1h continuation with wider stops)
- Or leave SCALP bear slot empty / cash until a non-falsified candidate appears
