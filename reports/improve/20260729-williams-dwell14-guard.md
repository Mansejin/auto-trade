# Williams v1 — sideways dwell >=14d guard recheck

Date: 2026-07-29  
Strategy: `strategies/regime-sideways-mr-1h-williams-v1.json` (thresholds frozen)

## Guard definition
- Daily regime = sideways (same Binance 1d ADX/SMA map as before)
- `dwell` = consecutive sideways calendar days
- **Allow** only when `dwell >= 14`
- Backtest proxy: toolkit run on `[first_day_with_dwell_14, stretch_end]`
- Stretches with 0 allow-days => **FILTERED** (no BT)

## Comparison table

| Tag | Full stretch | Ungated (prior) | Dwell>=14 window | Gated result | Fail-case filter? |
|---|---|---|---|---|---|
| SW-new1 | 2025-01-29~02-06 (9d) | +0.84% / PF9.97 / n=3 | — | **FILTERED** | short stretch blocked |
| SW-new2 | 2025-04-04~04-25 (22d) | **-1.38% / PF0.61 / n=6** | 2025-04-17~04-25 (9d) | **+0.24% / PF inf / n=2 / WR100%** / bench +10.38% | **Partial** — early loss cut; late stub still trades |
| SW-old1 | 2025-06-05~07-13 (39d) | +0.58% / PF1.85 / n=12 | 2025-06-18~07-13 (26d) | **-0.96% / PF0.87 / n=7** / bench +9.60% | guard **hurts** this window |
| SW-A | 2025-08-05~08-15 (11d) | +1.57% / n=6 | — | **FILTERED** | short stretch blocked |
| SW-old2 | 2025-08-20~10-02 (44d) | +0.61% / PF1.53 / n=24 | 2025-09-02~10-02 (31d) | **+0.17% / PF1.99 / n=15** / bench +10.28% | still pass (smaller ret) |
| SW-B | 2025-12-29~01-05 (8d) | +0.15% / n=1 | — | **FILTERED** | short stretch blocked |
| SW-old3 | 2026-03-24~04-22 (30d) | +0.54% / PF1.51 / n=9 | 2026-04-06~04-22 (17d) | **+0.42% / PF inf / n=1** / bench +8.49% | pass but sparse |
| SW-new3 | 2026-07-23~07-28 (6d) | **-4.07% / PF0.03 / n=4** | — | **FILTERED** | **Yes** — Jul stub blocked |

## Target fail cases

| Case | Filtered by dwell>=14? |
|---|---|
| Apr-2025 (SW-new2) ungated PF 0.61 | **Not fully.** Stretch is 22d so days 14–22 remain. Gated subwindow alone was **+0.24% / 2 wins** (early drawdown removed). |
| Jul-2026 stub (SW-new3) ungated PF 0.03 | **Yes.** 6d < 14 => FILTERED. |

## Side effects (important)
- **SW-old1**: ungated pass -> gated **fail** (PF 0.87). Edge was partly in the first 13 sideways days.
- Short green stubs (new1 / SW-A / SW-B) also FILTERED (fewer false confidence samples, less activity).
- Gated passes that remain: old2 (solid), old3 (1 trade), new2 gated stub (2 trades).

## Verdict
- Dwell>=14 is a **useful anti-stub filter** (kills Jul-2026 fail; shrinks Apr-2025 damage).
- It is **not free**: can remove good early-stretch trades (old1).
- Research stance: keep as **optional mount guard** for paper-log, not a promote-to-LIVE reason by itself.
- Do not retune Williams thresholds from this table.

LIVE / Policy C unchanged.
