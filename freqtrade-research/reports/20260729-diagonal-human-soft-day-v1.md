# 빗각 Human-Soft day — discretionary-style forgiveness (BTC 15m) — 2026-07-29

## Intent

Prior bots took every rail match. Humans **용인**: wick pierce OK if close reclaims,
skip ugly angles/widths, don't spam touches.

## Spec (frozen)

| Item | Value |
|------|-------|
| Base rails | V1 volume-pivot + day liquidity |
| Pierce tol | 0.40% beyond rail (close must reclaim) |
| Quality | width 0.5–2.5% of mid; \|slope\| ≤ 0.12%/bar |
| Cooldown | 4×15m between entries |
| SL / ROI | −0.8% / +1.2% |
| Code | `DiagonalHumanSoftDayV1.py` |
| Config | `config.bitget-diagonal-human-soft-v1.json` |

## Results

| Window | Trades (avg/day) | Profit | PF | Market | Verdict |
|--------|------------------|--------|-----|--------|---------|
| W1 05-15→05-29 | 39 (2.79) | −1.81% | 0.77 | −9.5% | **fail** |
| W2 06-15→06-29 | 24 (1.71) | −2.55% | 0.66 | −9.5% | **fail** |
| W3 07-01→07-15 | 27 (1.93) | −0.74% | 0.89 | +10.7% | **fail** |

**Falsified** (3/3). Frequency got closer to 2–3/day; expectancy did not.

## Read

Forgiveness without a human **skip filter** just adds more marginal touches.
Quality gates on width/slope were not enough to recreate discretionary edge.
Next human-like step is **alert-only** (bot proposes, human vetoes) — the skip
filter is the part we cannot encode from OHLC alone.

## Lineup so far (auto-entry)

| Encoding | Gate |
|----------|------|
| LR scalp / V1 / V1-gate / Human-Soft | falsified |
| V2 Mode B | weak PF survive, too sparse, not promoted |
