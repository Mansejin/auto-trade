# SCALP (단타) live playbook — Bitget 50%

> Pair with 장타 CORE Upbit (`docs/regime-auto-switch-playbook.md`).  
> Source of truth: `config/sleeves.json` + `config/scalp-live-map.json`.

## Status (2026-07-30)

**SCALP LIVE = OFF (cash).**  
`bitget-futures-bot` stopped on Oracle. Compose profile `scalp` — default `docker compose up -d` does not start it.

Reason: second-opinion review — Div ATR bear “defense” (+2.3% vs BTC −43% on paper) is too fee/slippage/TF-drift fragile; cash dominates for bear scalp until a card re-passes falsification.

| Sleeve | Venue | Bot | LIVE |
|--------|-------|-----|------|
| 장타 CORE | Upbit spot | `upbit-paper-bot` famous mount | **ON** |
| 단타 SCALP | Bitget UTA | `bitget-futures-bot` | **OFF / cash** |

Capital intent remains 장타50:단타50 when SCALP is later re-enabled; until then idle Bitget USDT is just parked cash. No TRX rebalance below 50만 KRW total.

## Regime map (parked)

| Regime | LIVE |
|--------|------|
| all | **null / cash** |

Parked refs: `bitget-scalp-div-atr-v1`, `SidewaysEdge15mBbFadeV5` (research only).

## Re-enable (human only)

```bash
ssh auto-trade-bot 'cd ~/auto-trade && docker compose --profile scalp up -d bot-bitget'
```

Only after a new card passes multi-window falsification + explicit approve.
