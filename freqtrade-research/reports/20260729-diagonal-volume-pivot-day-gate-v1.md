# 빗각 V1-gate — Mode A + soft daily direction (BTC 15m) — 2026-07-29

## Spec (frozen)

| Item | Value |
|------|-------|
| Base | V1 Mode A volume-pivot + liquidity (no retune) |
| Gate | Policy-C daily regime on **Binance** BTC 1d |
| Soft rule | bull→long only; bear→short only; **else→both** |
| Pair / TF | `BTC/USDT:USDT` 15m |
| Code | `DiagonalVolumePivotDayGateV1.py` |
| Config | `config.bitget-diagonal-day-gate-v1.json` |

Hypothesis: blocking counter-trend Mode A touches lifts PF while keeping ~V1 trade frequency on non-trend days.

## Results

| Window | Trades (avg/day) | L/S | Profit | PF | Market | Verdict |
|--------|------------------|-----|--------|-----|--------|---------|
| W1 05-15→05-29 | 35 (2.5) | 17/18 | −0.71% | 0.90 | −9.5% | **fail** |
| W2 06-15→06-29 | 9 (0.64) | 0/9 | +2.16% | 2.58 | −9.5% | pass (bear shorts only) |
| W3 07-01→07-15 | 16 (1.14) | 0/16 | −2.89% | 0.53 | +10.7% | **fail** (bear gate vs rally) |

**Falsified** (≥2/3 PF&lt;1 / net&lt;0).

## Read

- Frequency: W1≈V1; W2/W3 collapse when regime is one-sided.
- W2 shows the intended effect (shorts only in bear → PF 2.58).
- W3: daily still **bear** while spot rallied +10% → gate forced shorts into the bounce. Soft else=both did not help once classified bear.
- W1: gate barely changed mix vs V1; longs still bled.

## Compare

| | V1 | V2 | V1-gate |
|--|----|----|---------|
| W1 PF | 1.06 | 0.66 | 0.90 |
| W2 PF | 0.79 | 1.10 | 2.58 |
| W3 PF | 0.60 | 1.16 | 0.53 |
| Gate | falsified | weak survive | **falsified** |
| Trades/day | 1.5–2.6 | 0.5–1.3 | 0.6–2.5 |

## Do not

- Retune regime ADX/SMA thresholds after this.
- Promote to LIVE / SCALP.

## Next

1. **Alert-only** — closest match to discretionary 빗각.
2. V2 longer OOS (still research-only).
3. Stop encoding short-TF 빗각 for auto-entry.
