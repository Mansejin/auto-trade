# SCALP (단타) live playbook — Bitget 50%

> Pair with 장타 CORE Upbit (`docs/regime-auto-switch-playbook.md`).  
> Source of truth: `config/sleeves.json` + `config/scalp-live-map.json`.

## Status (2026-08-06)

| Sleeve | Venue | Bot | LIVE |
|--------|-------|-----|------|
| 장타 CORE | Upbit spot | `upbit-paper-bot` Policy C | **ON** (병행) |
| 단타 SCALP | Bitget UTA futures | `bot-ft-scalp` → Freqtrade `TrendShortV1` | **bear only** |

- **Bear:** `di_cloud` ADX≥15 / SL 3% / TP 9% (`fingerprint 16dba43a38f9f882`)
- Bull / transition / sideways scalp: **cash** (`null`)
- `bot-bitget` toolkit = **롱만** 가능 → 이 숏에 쓰지 말 것

Fee note: backtest bar = 6bps/side; **fails 8bps stress** — human accepted RESEARCH_KEEP → LIVE. Prefer small fixed stake (`stake_amount: 100` USDT).

## Regime map

| Regime | LIVE card |
|--------|-----------|
| bear | `bitget-btc-5m-trend-short-di-cloud-adx15-v1` |
| bull / transition / sideways | null (cash) |

## Enable (human)

On the host that runs compose (credentials already in FT live config):

```bash
cd ~/auto-trade   # or repo root
git pull

# Put Bitget API key/secret/passphrase into:
#   freqtrade-research/user_data/config.bitget-scalp-trend-short-live.json
# (do not commit secrets)

chmod +x scripts/start-scalp-trend-short.sh
./scripts/start-scalp-trend-short.sh
# equivalent:
# docker compose --profile scalp up -d bot-ft-scalp
```

Verify:

```bash
docker compose --profile scalp ps bot-ft-scalp
docker compose --profile scalp logs -f bot-ft-scalp
```

Stop:

```bash
docker compose --profile scalp stop bot-ft-scalp
```

CORE Upbit is unchanged by these commands (`docker compose up -d` without `--profile scalp` does not start FT scalp).

## Files

| Role | Path |
|------|------|
| Map | `config/scalp-live-map.json` |
| Card | `strategies/bitget-btc-5m-trend-short-di-cloud-adx15-v1.json` |
| FT config | `freqtrade-research/user_data/config.bitget-scalp-trend-short-live.json` |
| Strategy class | `freqtrade-research/user_data/strategies/TrendShortV1.py` |
| Compose | `bot-ft-scalp` profile `scalp` |

## Roll back to cash

1. `docker compose --profile scalp stop bot-ft-scalp`
2. Set `config/scalp-live-map.json` `map.bear` → `null`, `status` → `stopped_cash`
3. Commit when intentional
