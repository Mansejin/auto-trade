# Weekly CORE observation (Policy C only)

> No map/ADX retune. Observe only. SCALP stays OFF.

## Cadence

**Once per week** (any quiet day):

```powershell
cd C:\Users\Ohola\Documents\GitHub\auto-trade
python scripts/weekly_core_obs.py
# optional remote bot snapshot:
python scripts/weekly_core_obs.py --ssh
```

Writes `reports/ops/weekly-core-obs-YYYYMMDD.md`.

## Checklist (human)

1. Regime vs expected Policy C file — match?
2. Upbit bot healthy, flat or position intentional?
3. SCALP / bitget still **stopped**?
4. Any urge to tweak ADX/map? → **No. Log only.**
5. Seed still going to **Upbit only**?

## Not in scope

- Parameter shopping, Div ATR revive, leverage, rebalance under 50만 KRW.
