# Deep validation — Bitget BTC 5m swing short

**Status: RESEARCH_KEEP** (not LIVE)

Base: `di_cloud` / ADX≥15 / SL3% / TP9%  
FT: stake=100, `use_order_book=false`, fee=6bps/side

## Verdict summary

| Check | Result |
|-------|--------|
| h1 + h2 PF≥1.2 @ 6bps | PASS (1.44 / 1.20) |
| Full sample PF | 1.31 / n60 / DD 2.38% |
| Quarters PF≥1.0 | 4/4 (1.19, 2.45, 1.13, 1.47) — thin n |
| Fee stress dual-half ≥1.2 | PASS @0 & 6bps; FAIL @10 & 12bps |
| Neighbors FT pass | 4/7 |
| Ablation | Cloud load-bearing on h2; ADX25 fails h2 |

Fragile: marginal h2, fee sensitivity, small quarterly samples.

## Artifact

- `deep-summary.json` — full numbers
- Canvas: `bitget-btc-swing-short-deep.canvas.tsx`
