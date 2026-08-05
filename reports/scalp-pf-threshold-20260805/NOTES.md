# Scalp PF threshold judgment (2026-08-05)

## Is PF 1.1 meaningful for ultra-short?

**After fees only, and only with enough trades.**

| Condition | Meaningful? |
|-----------|-------------|
| After-fee PF >= 1.10 and n >= 150 / OOS half | Yes - weak but bankable bar for ranking |
| After-fee PF >= 1.15 and n >= 100 / half | Yes - preferred when n is thinner |
| fee=0 PF ~ 1.13 | No - 12bps RT wipes it (fee is 15-40% of a 0.3-0.8% scalp move) |

Break-even after fees is PF=1.0. 1.1 means ~10% more win absolute than loss absolute (fixed notional).

## Re-search result (fee 6bps/side)

- Primary PF>=1.10 n>=150: **5m hits=0** (best ~0.93), **1m hits=0** (best ~0.86)
- Strict PF>=1.15 n>=100: **5m hits=0**

Conclusion: ultra-short shorts on this Bitget BTC window have **no meaningful after-fee edge** under either bar. Keep the 5m **swing** HIT (SL3%/TP9%, ~30 trades/half) instead.
