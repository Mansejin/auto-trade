# Dual-sleeve capital allocation (장타 CORE + 단타 SCALP)

> Intent: **split capital**, not replace Policy C.  
> Config: [`config/sleeves.json`](../config/sleeves.json) · SCALP map: [`config/scalp-live-map.json`](../config/scalp-live-map.json) · Race: [`research/famous-vs-policyC-race.md`](research/famous-vs-policyC-race.md)

## Live posture (2026-07-31)

| Sleeve | Venue | LIVE | Capital handling |
|--------|-------|------|------------------|
| **CORE 장타** | Upbit | **ON** (Policy C) | **Seed here** |
| **SCALP 단타** | Bitget | **OFF / cash** | Ignore dust; do not fund |

Intent weights remain 50:50 for when SCALP is later re-enabled. Until then treat the book as **Upbit-only CORE**.

## Seed policy (simple)

1. New deposits → **Upbit only**.
2. Do not TRX-bridge to Bitget while SCALP is stopped.
3. No rebalance if total &lt; **500,000 KRW** (`REBALANCE_MIN_TOTAL_KRW`).
4. Bitget leftover USDT/TRX = ignore until a scalp card is promoted again.

## Split (frozen intent)

| Sleeve | Venue | Role | Intent % |
|--------|-------|------|----------|
| CORE | Upbit spot | Policy C | 50 |
| SCALP | Bitget UTA | cash until re-promotion | 50 |

## Weekly observe

See [`docs/ops/weekly-core-obs.md`](ops/weekly-core-obs.md) — regime / path / bot health only. No map retune.

Design (not LIVE): major-bull re-entry gate + Bitget lev swing/hedge — [`bull-reentry-and-lev-hedge.md`](bull-reentry-and-lev-hedge.md).

## Policy C evidence (short)

- In-sample fair race (2021–26): strong vs hold on return **and** MDD.
- OOS presample (2018–21 aligned): return ≈ hold; **MDD still better**.
- Fee stress 2×: see `docs/research/policyC-fee-stress-2x.md` (after script run).
