# AE14 — Paper-log spec (research shelf only)

> Event rules for **H1 funding** + **H_rich premium fade**.  
> **Not** a strategy JSON. **No** Policy C / `STRATEGY_PATH` / LIVE wiring.  
> Not investment advice.

## Purpose

Log hypothetical fills when frozen shelf rules fire, so forward sample can accumulate without promoting alpha. Scoring stays one-shot / time-holdout when enough events exist.

## Frozen rules (do not retune)

| Rule | Trigger | Paper action | Horizon | Cost budget |
|------|---------|--------------|---------|-------------|
| **H1** | `fundingRate <= -0.0002` | Long KRW-BTC (spot notionally) | Next UTC day close→close | **20 bps** RT primary (fee+slip) |
| **H_rich** | Upbit `premium >= 0.004563` (AE13 train 90th) | Fade = short / skip-long KRW-BTC | Next UTC day | **20 bps** RT primary |

Premium: `KRW-BTC / (USDT-BTC × KRW-USDT) − 1`.

## Source isolation (critical)

| Role | Source | Notes |
|------|--------|-------|
| H1 **history** study | **HTX** only | Already scored (AE12b/c). Do not re-pool. |
| H1 **forward** log | OKX **and/or Bitget** | Separate JSONL + `source` tags. **Never** mix venues into one test without a new AE id. |
| H_rich | Upbit internal markets only | Orthogonal to perp funding. |
| H2 OB | Upbit orderbook imbalance | Still gated: collect ≥336 rows. |

Bitget MCP snapshot (2026-07-29T06:18Z): current funding **+0.000064** (interval 8h); last 50 hist prints **0** hits of `<= -0.0002` (min ≈ −0.000118). Forward H1 events will be **sparse** on Bitget — expected.

## Paper fill model

1. On trigger at snapshot `ts_utc`, record `signal_date` = UTC calendar date of `ts_utc`.
2. Default PnL window matches AE12b/AE13: signal day → next UTC-day KRW-BTC return.
3. Gross PnL: long `fwd_1d`; fade `-fwd_1d`.
4. Net PnL: gross − `0.0020` (20 bps). Stress ladder optional: 10/20/30/50 (same as AE12c/AE13b).
5. Gap risk: weekend/holiday gaps are **in** the daily return; no stop. Size later; default log-only (null notional).

## Logs (gitignore JSONL)

| File | Content |
|------|---------|
| `reports/ae12-collect/okx-funding.jsonl` | existing AE12 collector |
| `reports/ae12-collect/bitget-funding.jsonl` | Bitget UTA `BTCUSDT` fund rate + mark/index |
| `reports/ae12-collect/upbit-orderbook.jsonl` | existing (H2) |
| `reports/ae14-paper/upbit-premium.jsonl` | premium components |
| `reports/ae14-paper/paper-events.jsonl` | fires only |

Scripts: `scripts/ae12_forward_collect.py`, `scripts/ae14_paper_log.py`.

```cron
*/30 * * * * cd ~/auto-trade && python3 scripts/ae12_forward_collect.py >> logs/ae12-collect.cron.log 2>&1
*/30 * * * * cd ~/auto-trade && python3 scripts/ae14_paper_log.py >> logs/ae14-paper.cron.log 2>&1
```

## Promotion gate (unchanged)

Paper retain ≠ promote. LIVE / Policy C only after new AE id (if venue-pooled), walk-forward + `strategy_audit.py` if mounted, and human approve.

## AE15 (registered, not scored)

**Hyp (frozen):** Bitget USDT-perp **mark−index basis** `(markPrice/indexPrice − 1)` rich tail predicts next-day KRW-BTC **underperformance** vs baseline (orthogonal to Upbit KRW premium; not funding-cut mining).

**Falsify:** Train 70% fits **train 90th basis cut only**; holdout last 30%: if rich-event mean ≥ baseline mean **or** hit ≥ baseline hit → falsified. Min holdout events = 8. One shot; no cut sweep after returns.

**Defer:** Bitget funding `<= -0.0002` venue-confirm of H1 — same cut, Bitget-only sample; do not merge HTX. Likely underpowered (MCP hist rarely hits cut).

## Explicit non-goals

- No auto market-sell on regime switch
- No SMA ±3% buffers / transition→sideways without Policy re-backtest
- No AE6–AE11 TA restart
- No refit of funding `-0.0002` or premium `0.004563`
