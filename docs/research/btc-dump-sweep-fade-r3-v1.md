# btc-dump-sweep-fade-r3-v1 — FALSIFIED

Always-on BTC dump sweep → reclaim fade (no calendar). CORE overlay candidate — **not LIVE**.

## Frozen

| Field | Value |
|-------|--------|
| Detect | 4×15m low &lt; prior 20-bar low AND range ≥ 2×ATR14 |
| Entry | close back above broken level within 4 bars |
| Regime | bull / transition long only |
| SL / TP | 0.5% / 1.5% (1:3) |
| Cooldown | 6h |
| Fee | 0.06%×2 |
| Script | `scripts/bt_btc_dump_sweep_fade_r3.py` |
| Artifact | `reports/bt-btc-dump-sweep-fade-r3-20260731_053257.json` |

## Result (Binance BTCUSDT-M 15m, 2021–2026)

| Slice | n | WR | PF | compound |
|-------|--:|---:|---:|---------:|
| all | 1353 | 26.8% | **0.76** | −78.5% |
| train | 947 | 26.5% | 0.76 | −66% |
| holdout | 406 | 27.3% | **0.76** | −37% |

TP/SL ≈ 324 / 983 — R:R 1:3 does not overcome ~27% hit rate after fees.

## Verdict

**FALSIFIED** on train and holdout. Same character as calendar sweep-fade but worse once always-on (many more losers). Do not promote; do not shop SL/TP on this id.
