# 5m RSI-BB scalp long/short v4

## Intent
Bitget BTCUSDT-M futures style dual mean-reversion scalp (research only).
Upbit toolkit is long-only / `kr` only — short file is an **entry-timing proxy** (buys on overbought), not a true short PnL sim.

## Frozen rules
| Side | Entry | Exit |
|---|---|---|
| Long | RSI(14) < 25 AND close < BB lower(20,2) AND ADX(14) < 30 | TP +0.8% / SL -0.3% only |
| Short (Bitget) | RSI(14) > 75 AND close > BB upper(20,2) AND ADX(14) < 30 | TP +0.8% / SL -0.3% only |

## Cost model (Bitget)
- Taker 0.06% × 2 = 0.12% RT
- Slip stress ~0.02–0.04% RT → total ~0.14–0.16%
- Net: win ≈ +0.68%, loss ≈ −0.42% → breakeven WR ≈ **38%** (vs 52% at TP 0.5)

## Proxy caveat (short)
`krw-btc-5m-scalp-rsi-bb-short-proxy-v4.json` enters long on overbought.
- TP hit = price continued up → real short would hit SL
- SL hit = price fell ≥0.3% → real short would be in profit (not full TP 0.8)
Use SL/TP hit counts as directional evidence; do not treat proxy Total Return as short PnL.

## Falsification
- Either side: WR < 38% or PF < 1.0 across ≥2 of 3 OOS windows
- Do not mount to LIVE / Policy C from this alone
