# Williams v1 — multi-window expansion (2026-07-29)

Strategy: `strategies/regime-sideways-mr-1h-williams-v1.json`  
Fee: toolkit default. Windows labeled by **daily** regime (Binance BTCUSDT-M ADX/SMA map).

## Sideways (mount target)

| Tag | Period | Trades | WR | PF | Return | Bench | Pass* |
|---|---|---|---|---|---|---|---|
| SW-new1 | 2025-01-29~02-06 | 3 | 67% | 9.97 | **+0.84%** | -2.54% | Y (sparse) |
| SW-new2 | 2025-04-04~04-25 | 6 | 83% | **0.61** | -1.38% | +9.88% | N |
| SW-old1 | 2025-06-05~07-13 | 12 | 75% | 1.85 | +0.58% | +9.89% | Y |
| SW-old2 | 2025-08-20~10-02 | 24 | 79% | 1.53 | +0.61% | +5.68% | Y |
| SW-old3 | 2026-03-24~04-22 | 9 | 78% | 1.51 | +0.54% | +7.14% | Y |
| SW-new3 | 2026-07-23~07-28 | 4 | 25% | **0.03** | -4.07% | -3.85% | N (short/noisy) |

\*Pass = return&gt;0 and PF≥1 and trades≥5 (new1 fails trades≥5; listed Y-sparse).

**Sideways score:** clear pass 3/6 (old1–3); soft/sparse 1/6 (new1); fail 2/6 (new2, new3).  
Earlier “3/3” was not fully OOS-stable after expansion.

## Contrast (should not be primary mount)

| Tag | Regime | Period | Trades | PF | Return | Bench |
|---|---|---|---|---|---|---|
| BEAR1 | bear | 2025-11-17~12-28 | 16 | 1.26 | -0.23% | -9.70% |
| BEAR2 | bear | 2026-01-21~03-04 | 18 | 1.29 | +0.49% | -24.65% |
| BEAR3 | bear | 2026-05-28~07-14 | 19 | **0.37** | -9.96% | -15.75% |
| BULL1 | bull | 2025-07-20~07-31 | 6 | **0.46** | -1.78% | +1.07% |
| TRANS1 | transition | 2025-04-26~06-04 | 18 | 2.14 | +2.65% | +7.79% |
| TRANS2 | transition | 2026-04-23~05-22 | 11 | 0.93 | -1.26% | -1.27% |

## Interpretation (facts)
- Still often green in longer sideways stretches (Jun–Jul / Aug–Oct 2025, Mar–Apr 2026).
- New Apr-2025 sideways and Jul-2026 stub **break** PF≥1 — retain bar no longer unanimous.
- Bear windows: sometimes PF&gt;1 with flat/small P&amp;L (BH much worse); May–Jul 2026 bear **hurts**.
- Bull window failed; transition mixed.
- Strategy still trails buy&amp;hold inside many sideways up-drifts.

## Status
- Keep as **research shelf** candidate, not LIVE.
- Do not promote on “all sideways work” claim.
- Optional next: require min sideways dwell (e.g. ≥14d) before mount; paper-log only on dwell≥14d days.

LIVE / Policy C unchanged.
