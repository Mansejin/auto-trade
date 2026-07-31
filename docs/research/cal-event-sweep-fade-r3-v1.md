# cal-event-sweep-fade-r3-v1

> Overlay ≠ CORE. **LIVE auto not armed** (train failed despite holdout).

## Frozen

| Field | Value |
|-------|--------|
| Events | FOMC / CPI / NFP |
| Vol gate | first 60m range ≥ 2× ATR14 |
| Entry | sweep of first-hour high/low → close back inside within 4×15m (1-shot) |
| Direction | bull/transition → long on failed low sweep; bear → short on failed high sweep; side skip |
| SL / TP | 0.5% / 1.5% (1:3) |
| Fee | 0.06%×2 |
| Script | `scripts/bt_cal_event_sweep_fade_r3.py` |
| Artifact | `reports/bt-cal-event-sweep-fade-r3-20260731_053027.json` |

## Result (Binance BTCUSDT-M 15m, 2021–2026)

| Slice | n | WR | PF | compound | TP/SL/time |
|-------|--:|---:|---:|---------:|------------|
| all | 57 | 29.8% | 0.88 | −3.1% | 14/39/4 |
| train 70% | 39 | 28.2% | **0.78** | −3.9% | 8/27/4 |
| holdout 30% | 18 | 33.3% | **1.12** | +0.8% | 6/12/0 |

## Verdict

- Holdout: **SURVIVES** (narrow, n=18).
- Train + all: **fail** (PF&lt;1).
- vs prior R10 reclaim card: much less bad (TP actually hits), but **not robust enough to auto-LIVE**.

Next (human only): more out-of-sample years, or paper dry-run — **no SL/TP shopping** on this id. New id if entry rule changes.
