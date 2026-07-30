# SCALP (단타) live playbook — Bitget 50%

> Pair with 장타 CORE Upbit 50% (`docs/regime-auto-switch-playbook.md`).  
> Source of truth: `config/sleeves.json` + `config/scalp-live-map.json`.

## Capital

| Sleeve | Venue | % | Bot |
|--------|-------|---|-----|
| 장타 CORE | Upbit spot | 50 | `upbit-paper-bot` Policy C |
| 단타 SCALP | Bitget UTA futures | 50 | `freqtrade-scalp` |

Venue split = sleeve split → **빗겟:업비트 5:5**.

## SCALP regime map (LIVE)

| Regime | Strategy | Config |
|--------|----------|--------|
| `bear` | `DaytradeEdge10mDivAtrV1` (15m port; Bitget has no 10m) | `config.bitget-scalp-div-atr-live.json` |
| `sideways` | `SidewaysEdge15mBbFadeV5` | `config.bitget-scalp-side-fade-live.json` |
| `bull` / `transition` | **flat / stop** | cash |

Pointer: `freqtrade-research/user_data/ACTIVE_SCALP_STRATEGY`

Upbit JSON refs (research / audit):  
`strategies/daytrade-edge-10m-div-atr-v1.json`,  
`strategies/daytrade-edge-side-15m-bb-fade-v5.json`

## Switch (local / remote Bitget bot)

```powershell
cd freqtrade-research
# example: bear
echo DaytradeEdge10mDivAtrV1 > user_data/ACTIVE_SCALP_STRATEGY
.\.venv\Scripts\freqtrade.exe download-data -c user_data/config.bitget-scalp-div-atr-live.json --trading-mode futures -t 10m --timerange 20260501-
# dry-run trade (LIVE keys only after human approve):
.\.venv\Scripts\freqtrade.exe trade -c user_data/config.bitget-scalp-div-atr-live.json --strategy DaytradeEdge10mDivAtrV1
```

Do **not** point `upbit-paper-bot` STRATEGY_PATH at these.

## Empty slots → automation

Bull scalp + bear **short** slots remain open.  
Hunt via `docs/scalp-short-edge-automation-prompt.md` (mirrors banned).
