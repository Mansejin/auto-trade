# AE12 / AE14 forward collection

Append-only snapshots for later event studies. **Not** a live alpha.

## Collect

```bash
python3 scripts/ae12_forward_collect.py   # market snaps
python3 scripts/ae14_paper_log.py         # frozen rule → paper-events (no orders)
```

Writes (JSONL gitignored):

- `reports/ae12-collect/okx-funding.jsonl`
- `reports/ae12-collect/bitget-funding.jsonl` (UTA v3 + mark/index basis)
- `reports/ae12-collect/upbit-orderbook.jsonl`
- `reports/ae14-paper/upbit-premium.jsonl`
- `reports/ae14-paper/paper-events.jsonl` (only when H1 / H_rich fires)

Suggested cron (UTC), every 30 minutes:

```cron
*/30 * * * * cd ~/auto-trade && python3 scripts/ae12_forward_collect.py >> logs/ae12-collect.cron.log 2>&1
*/30 * * * * cd ~/auto-trade && python3 scripts/ae14_paper_log.py >> logs/ae14-paper.cron.log 2>&1
```

**Source isolation:** OKX / Bitget / HTX must not be pooled into one H1 test without a new AE id. HTX = history study only; OKX+Bitget = forward logs.

## Readiness / study

```bash
python3 scripts/ae12_event_study.py
```

Frozen hypotheses (do not retune after collection starts):

1. `fundingRate <= -0.0002` → next UTC day KRW-BTC mean return > baseline  
2. `|orderbook imbalance| >= 0.4` → next 1h move (signed by imbalance) beats baseline  

H2 needs `upbit-orderbook.jsonl` ≥ 336 rows. Holdout: last 30% by time.

Paper-log spec: `reports/improve/20260729-ae14-paper-log-spec.md`

## Related

- Lag MDD: `scripts/ae12_lag_mdd.py`
- Bitget MCP (Cursor): `market` verb `fundingRate` / `tickers` / `orderbook` — read-only snapshot aid; cron still uses REST in this script.
