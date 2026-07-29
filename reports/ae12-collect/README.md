# AE12 forward collection

Append-only snapshots for later event studies. **Not** a live alpha.

## Collect

```bash
python3 scripts/ae12_forward_collect.py
```

Writes:

- `reports/ae12-collect/okx-funding.jsonl`
- `reports/ae12-collect/upbit-orderbook.jsonl`

Suggested cron (UTC), every 30 minutes:

```cron
*/30 * * * * cd ~/auto-trade && python3 scripts/ae12_forward_collect.py >> logs/ae12-collect.log 2>&1
```

## Readiness / study

```bash
python3 scripts/ae12_event_study.py
```

Frozen hypotheses (do not retune after collection starts):

1. `fundingRate <= -0.0002` → next UTC day KRW-BTC mean return > baseline  
2. `|orderbook imbalance| >= 0.4` → next 1h move (signed by imbalance) beats baseline  

Holdout rule: last 30% of collection span by time.

## Related

- Lag MDD (Policy C switch pain): `scripts/ae12_lag_mdd.py` → `reports/improve/20260729-ae12-lag-mdd.md`
