# Timeframe-Specific Default Periods

Default-period table automatically applied by the backtest skill when the user does not explicitly specify a period. Details for SKILL.md STEP 2.

> **Only the backtest skill owns period selection.** Even in create-strategy handoff, do not pass a period - pass only `timeframe` and decide from this table. This keeps period selection in one place so two skills cannot compute conflicting periods.

---

## 1. Calculation Principles

Three base anchors:

| timeframe | Period | Candle count (approx.) |
|---|---|---|
| `1d` | last 1 year | ~365 candles |
| `1h` | last 3 months | ~2,160 candles |
| `1m` | last 1 week | ~10,080 candles |

Other timeframes are calculated around **roughly 250 candles**.

---

## 2. Full 13-Timeframe Default Table

| timeframe | Default period | Candle count (approx.) | Notes |
|---|---|---|---|
| `1M` | last 3 years | 36 candles | Monthly candles - suitable for trend-hypothesis validation. Longest backtestable timeframe |
| `1w` | last 2 years | 104 candles | Weekly candles - medium-term hypotheses |
| `1d` | **last 1 year** | ~365 candles | Anchor |
| `4h` | last 6 months | ~1,080 candles | |
| `1h` | **last 3 months** | ~2,160 candles | Anchor |
| `30m` | last 1.5 months | ~2,160 candles | |
| `15m` | last 1 month | ~2,880 candles | |
| `10m` | last 3 weeks | ~3,024 candles | |
| `5m` | last 2 weeks | ~4,032 candles | |
| `3m` | last 10 days | ~4,800 candles | |
| `1m` | **last 1 week** | ~10,080 candles | Anchor |
| `1s` | **last 1 day** | ~86,400 candles | Very heavy - recommend checking whether the user really needs it |

Each row converges around roughly 1,000-10,000 candles. Only 1M/1w have small candle counts, so their sample limitations are explicit.

---

## 3. Large Candle Count Warning Threshold

Warn the user once before calling for these cases:

| Pattern | Candle count | Recommendation |
|---|---|---|
| `1m` x 1 year | ~525,600 candles | Recommend 1 week to 1 month |
| `1s` x 1 week | ~604,800 candles | Recommend 1 to 3 days |
| `5m` x 5 years | ~525,600 candles | Recommend 1 year |

Example warning message:

```
The requested period will collect about N candles. Candle collection and cache load are high.
- Recommended: {timeframe-specific default}
- Proceed anyway?
```

---

## 4. start_date / end_date Calculation Rules

- `end_date` is **yesterday (today - 1, UTC)** unless the user specifies another reference date. The historical data service does not serve the current day (and current month) by spec, so today is never fully available. Anchoring the default end to yesterday avoids a guaranteed "candle data unavailable for {today}" warning on every default run.
- `start_date` is `end_date - {default period}` (YYYY-MM-DD date string - the tool parses it as UTC 00:00)
- Warmup candles are automatically supplemented by the tool before `start_date`. The skill does not apply separate adjustment.

Example: today = 2026-05-22, timeframe = 1d -> end_date = 2026-05-21, start_date = 2025-05-21

---

## 5. User Overrides

Ignore this table and use the user's value only when the user directly specifies a period in the utterance (for example, "6 months from 2024-01-01", "last 1 month"). Otherwise, use the table.

Same for create-strategy handoff paths - create-strategy does not send a period.
