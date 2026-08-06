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
- NAS host folder: `/volume1/docker/p3f8c1a2` · compose project `p3f8c1a2` · service **`w5`** (profile `scalp`)

Fee note: backtest bar = 6bps/side; **fails 8bps stress** — human accepted RESEARCH_KEEP → LIVE. Prefer small fixed stake (`stake_amount: 100` USDT).

## Regime map

| Regime | LIVE card |
|--------|-----------|
| bear | `bitget-btc-5m-trend-short-di-cloud-adx15-v1` |
| bull / transition / sideways | null (cash) |

## Enable on NAS (human / local SSH)

```bash
# from PC
ssh saenggibu-nas-local

cd /volume1/docker/p3f8c1a2
# Bitget keys must be in config.bitget-scalp-trend-short-live.json (inject from .env; never commit)

sudo /usr/local/bin/docker compose -p p3f8c1a2 -f docker-compose.nas.yml --profile scalp up -d w5
sudo /usr/local/bin/docker compose -p p3f8c1a2 -f docker-compose.nas.yml --profile scalp ps w5
sudo /usr/local/bin/docker compose -p p3f8c1a2 -f docker-compose.nas.yml --profile scalp logs -f w5
```

Stop:

```bash
sudo /usr/local/bin/docker compose -p p3f8c1a2 -f docker-compose.nas.yml --profile scalp stop w5
```

CORE `w1` is unchanged (no `--profile scalp` needed for normal desk/upbit).

## Files

| Role | Path |
|------|------|
| Map | `config/scalp-live-map.json` |
| Card | `strategies/bitget-btc-5m-trend-short-di-cloud-adx15-v1.json` |
| FT config | `freqtrade-research/user_data/config.bitget-scalp-trend-short-live.json` |
| Strategy class | `freqtrade-research/user_data/strategies/TrendShortV1.py` |
| NAS compose | `w5` profile `scalp` in `docker-compose.nas.yml` |

## Roll back to cash

1. Stop `w5`
2. Set `config/scalp-live-map.json` `map.bear` → `null`, `status` → `stopped_cash`
3. Commit when intentional
