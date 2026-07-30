# Regime daytrade-edge pack

> **2026-07-30:** promoted into **단타 SCALP live** (Bitget), not Policy C.  
> 장타 CORE remains Policy C on Upbit (`docs/regime-auto-switch-playbook.md`).

## SCALP live map

| Regime | Card (Bitget FT) | Upbit ref JSON |
|--------|------------------|----------------|
| **bear** | `DaytradeEdge10mDivAtrV1` | `daytrade-edge-10m-div-atr-v1.json` |
| **sideways** | `SidewaysEdge15mBbFadeV5` | `daytrade-edge-side-15m-bb-fade-v5.json` |
| **bull** | cash | — |

See `config/scalp-live-map.json` · `docs/scalp-live-playbook.md`.

## Closed / do not resume

- Bull 10m/15m pullback daytrade (v1–v9)
- `bull-swing-4h-ema21-reclaim-v1` (dominated by Policy C bull 4h)
- Long→short mirrors for SCALP short hunt (v13 falsified)

## Short slots

Open for `docs/scalp-short-edge-automation-prompt.md`.
