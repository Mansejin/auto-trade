# cal-event-vol-reclaim-r10-v1 — FALSIFIED

> Overlay only (not CORE). **Do not LIVE / do not auto-arm.**

## Frozen card

| Field | Value |
|-------|--------|
| Events | FOMC, CPI, NFP (`config/us-macro-calendar.json`) |
| TF | 15m |
| Vol gate | first 60m range ≥ 2× ATR14 |
| Regime | engine v2 prior day; bull/transition long, bear short, sideways skip |
| Entry | EMA20 reclaim / break (1-shot per window) |
| SL / TP | 0.4% / 4.0% (1:10) |
| Fee | 0.06%×2 |
| Intended venue | Bitget BTCUSDT-M, lev 3x (not tested in PnL %) |
| Mode | would be fully automatic — **blocked by falsification** |

## Result (Binance BTCUSDT-M 15m, 2021-01 → 2026-07)

| Slice | n | WR | PF | compound | TP / SL / time |
|-------|--:|---:|---:|---------:|----------------|
| all | 113 | 15.0% | **0.51** | −21.6% | 4 / 93 / 16 |
| train 70% | 79 | 13.9% | 0.52 | −16.0% | 3 / 67 / 9 |
| holdout 30% | 34 | 17.7% | **0.51** | −6.8% | 1 / 26 / 7 |

Artifact: `reports/bt-cal-event-vol-r10-20260731_052526.json`  
Script: `scripts/bt_cal_event_vol_r10.py`

## Verdict

**FALSIFIED** — holdout PF &lt; 1, avg ret &lt; 0, median R ≈ −1.3 (almost all stop-outs).  
1:10 payoff did not compensate; TP filled only 4/113 times.

Auto-trading path is **not enabled** on Oracle (motto: no promote after fail).  
Revision requires a **new card id** (different entry/window), not SL/TP shopping on this one.
