# 나씨 3틱 B + lev5 + TP 3%/5% — 2026-07-29

Card: [`docs/research/nassi-3tick-b-lev5-tp-card-frozen.md`](../../docs/research/nassi-3tick-b-lev5-tp-card-frozen.md)

Price ≈ profit / 5: TP +3% ≈ +0.6% px · TP +5% ≈ +1.0% px · SL −20% ratio ≈ **−4% px** (binding).

## vs B (lev1, TP 0.1%)

| Window | B | Lev5 TP3% | Lev5 TP5% |
|--------|---|-----------|-----------|
| May | +0.10% | **−1.38%** (PF 0.62) | **−0.55%** (PF 0.85) |
| Jun | +0.33% | **−3.99%** (PF 0.53) | **−7.21%** (PF 0.39) |
| Jul | +0.06% | +1.23% (PF 6.51) | +2.68% (PF 13.0) |

## Exit mix (stress)

- **TP3%**: May 10 reclaim / 2 SL · Jun 21 reclaim / **5 SL** · Jul 6 reclaim / 1 force  
- **TP5%**: May 10 reclaim / 2 SL · Jun 14 reclaim / **7 SL** · Jul 6 reclaim / 1 force  

SL avg ≈ **−12.6% ~ −13%** trade (lev-scaled). Wins avg ≈ +3.5~6.4%.

## Verdict

| Code | Falsify |
|------|---------|
| `…Lev5Tp03` | **Falsified** (2/3) |
| `…Lev5Tp05` | **Falsified** (2/3) |

Jul looks good; May/Jun stop clusters wipe the small-cycle edge B had. Higher TP + 5x makes SL (−20% ratio ≈ −4% price) **matter** — opposite of “SL too loose vs 0.1% TP” at 1x.

**Do not retune.** Prefer B for this line, or a **new** card that sets SL/TP RR explicitly in price space. No LIVE.
