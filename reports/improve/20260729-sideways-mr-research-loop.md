# Research loop 2026-07-29 — sideways MR hunt

## Retain bar (frozen before loop)
On ≥2/3 daily-sideways windows: PF≥1, WR≥40%, return&gt;0, trades≥5.  
Must not assume always-on 1h ADX filter = daily sideways.

## Tried ( falsified / weak )
| Slug | Note |
|---|---|
| adx-switch-v1 RSI+BB | SW3 PF0; sparse |
| bb-reclaim-v2 | SW3 PF0.29 |
| stochrsi-v2 | best prior; SW2 PF0.74 fail |
| stochrsi-bbmid-v3 | worse than v2 |
| stochrsi-holdmid-v4 | SW2 PF0.39 |
| cci-fade-v1 | mostly 0 trades |
| Bitget stoch L/S | shorts dragged |
| Bitget stoch long | inconsistent vs Upbit |

## Research retain (shelf only)
**`regime-sideways-mr-1h-williams-v1`**
- All 3 primary SW windows PF 1.51–1.85, WR 75–79%, return +0.5~0.6%
- Extra SW-A also green
- **Always-on bearish 3m: FALSIFIED (−20%)** → mount only via daily sideways regime
- Bitget FT: SW2/SW3 PF&gt;1, SW1 weak — venue not identical; Upbit is primary shelf

## Policy C / LIVE
Unchanged. Candidate registered as alt only.

## Next loop ideas (not done)
- Paper-log Williams when `regime-current==sideways`
- Audit vs `regime-sideways-mr-4h-v5` on same SW windows (activity vs stability tradeoff)
- Do **not** retune Williams thresholds on these results
