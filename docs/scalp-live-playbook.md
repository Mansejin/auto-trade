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

## LIVE host = Oracle `bot-bitget` (not local Freqtrade)

Production: `bitget-futures-bot` on `auto-trade-bot` (Oracle).  
Active file: `strategies/bitget-scalp-div-atr-v1.json` via `BITGET_STRATEGY_PATH` (Upbit CORE stays on `STRATEGY_PATH`).

```bash
scp strategies/bitget-scalp-div-atr-v1.json auto-trade-bot:~/auto-trade/strategies/
ssh auto-trade-bot 'cd ~/auto-trade && grep BITGET_STRATEGY_PATH .env && docker compose up -d bot-bitget'
```

Freqtrade ports under `freqtrade-research/` are research-only. Do **not** run `freqtrade trade` on the home PC for LIVE.  
Bitget API IP whitelist = Oracle egress, not your laptop.

## Empty slots → automation

Bull scalp + bear **short** slots remain open.  
Hunt via `docs/scalp-short-edge-automation-prompt.md` (mirrors banned).
