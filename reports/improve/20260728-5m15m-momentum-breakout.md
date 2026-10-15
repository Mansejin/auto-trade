# 5m/15m Momentum Breakout — ~0.5%/day hypothesis

> Toolkit stdout only. Fees on. No slippage / book / partial fills.  
> **Not investment advice. Past ≠ future.**

## Hypothesis

On KRW-BTC, **breakout/momentum** entries on 5m/15m (BB upper break or EMA/MACD cross
with ADX/DI confirmation) produce after-fee returns near **~0.5% per day**.

## Falsification

Default (recent) window far below ~0.5%/day path, **or** strong-bull window still
negative / far behind B&H → falsified for this family+risk budget.

## Recent window (toolkit defaults)

| Slug | Period | Total | B&H | MDD | PF | n |
|------|--------|------:|----:|----:|---:|--:|
| 5m BB breakout ADX25 | 07-13..27 | **-5.25%** | -0.16% | -6.93% | 0.64 | 36 |
| 5m EMA5/20 ADX20 | 07-13..27 | **-5.28%** | -0.16% | -5.98% | 0.88 | 50 |
| 15m BB breakout ADX25 | 06-27..07-27 | **-5.48%** | +4.09% | -5.91% | 0.28 | 17 |
| 15m MACD ADX22 | 06-27..07-27 | **-3.90%** | +4.09% | -3.90% | 0.27 | 18 |

→ **~0.5%/day FALSIFIED** on recent tape.

## Strong-bull stress (2024-11-03..2024-12-17)

| Slug | Total | B&H | PF | n |
|------|------:|----:|---:|--:|
| 5m BB breakout | **-11.64%** | +57.67% | 0.59 | 62 |
| 5m EMA ADX | **-7.61%** | +57.67% | 1.14 | 98 |
| 15m BB breakout | **-1.58%** | +57.71% | 1.12 | 32 |
| 15m MACD | **-4.30%** | +57.71% | 0.80 | 26 |

Even with +57% B&H, tight SL/TP breakout scalps **did not participate**.  
Same lesson as AE4: short-TF breakout ≠ 4h regime bull engine.

## Verdict

**Do not promote to LIVE.** Keep Policy C (`bull-v2` / `m5-v6` / `sideways-v5`).

## Files

- `strategies/krw-btc-5m-bb-breakout-adx25-sl06-tp12-v1.json`
- `strategies/krw-btc-5m-ema-adx20-mom-sl06-tp12-v1.json`
- `strategies/krw-btc-15m-bb-breakout-adx25-sl10-tp20-v1.json`
- `strategies/krw-btc-15m-macd-adx22-mom-sl10-tp20-v1.json`
