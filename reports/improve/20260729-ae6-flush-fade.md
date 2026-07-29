# AE6 — MFI + Williams flush-fade (first alpha track)

> Goal: find edge **beyond** Policy C SMA/ADX/RSI retunes.  
> Toolkit OHLCV only (no orderbook/OI scaffold yet).  
> Not investment advice.

## Hypothesis

When 4h **MFI < 20** and **Williams %R < -90** while **ADX < 35**, a short-term rebound occurs more often than a continued dump (volume-confirmed panic flush fade).

## Strategy

- File: `strategies/alpha-ae6-mfi-wr-flush-fade-4h.json`
- Buy: MFI<20 AND WR<-90 AND ADX<35
- Sell: MFI>55 OR WR>-30
- SL 3% / TP 5%
- Distinct from sideways-v5 (RSI+BB+ADX)

## Falsification criterion

Falsify as standalone alpha if early-OOS (prior 6m) has **PF < 1** and **total return ≤ 0**, or primary window has too few trades to trust (< 8) **and** longer window PF ≤ 1.

## Results (toolkit stdout; fees on; no slippage)

| Window | Period | Total | B&H | MDD | PF | WR | n |
|--------|--------|------:|----:|----:|---:|---:|--:|
| Primary (4h default ~6m) | 2026-01-29→2026-07-28 | **+2.67%** | -27.74% | -5.01% | 1.56 | 71% | **7** |
| Early OOS | 2025-07-29→2026-01-29 | **-4.74%** | -21.95% | -11.29% | **0.77** | 50% | 12 |
| 1y span | 2025-07-29→2026-07-28 | **-2.19%** | -43.60% | -11.29% | 0.98 | 58% | 19 |

## Verdict

**FALSIFIED as always-on / promote candidate.**

- Beats a sharply falling B&H on primary, but **n=7** is audit-sparse (G1).
- Early OOS loses money with **PF 0.77** → edge does not hold out of the recent window.
- 1y PF ≈ 1.0 with negative absolute return → no standalone alpha claim.

## Next (AE6b / AE7) — do not promote AE6

| id | idea | note |
|----|------|------|
| AE6b | Gate flush-fade only inside daily **bear/sideways** labels | May salvage as specialist; needs segment backtests before any map change |
| AE7 | One **non-price** feature (Upbit orderbook imbalance **or** Binance funding) with a written hypothesis first | Build fetcher only after hypothesis + falsify plan; no empty scaffold |

Do **not** retune MFI/WR thresholds to rescue primary — that is the overfitting path Gemini warned about.
