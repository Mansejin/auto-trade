# BTC Day-Box Fade V2 — 2026-07-29

Card: [`docs/research/btc-day-box-fade-v2-card-frozen.md`](../../docs/research/btc-day-box-fade-v2-card-frozen.md)

Anti-scrape vs V1: rejection wick + reclaim + stable width + cooldown; SL at wick extreme.

## Results vs V1

| Window | V1 trades / net | V2 trades / net | V2 mid/SL | Verdict |
|--------|-----------------|-----------------|-----------|---------|
| 2026-05 | 32 / **−16.9%** | 6 / **−2.95%** | 2 / 4 | **fail** |
| 2026-06 | 15 / **−20.2%** | 3 / **−6.04%** | 0 / 3 | **fail** |
| 2026-07 | 22 / **−12.1%** | 6 / **−4.15%** | 1 / 4 | **fail** |

**Falsified** (3/3).

## Read

- **긁힘 완화는 됨**: 거래 수·손실 폭 모두 V1 대비 축소.
- **엣지는 없음**: 남은 신호도 SL > mid. Expectancy still negative.
- Do **not** retune. Next card only if new hypothesis (e.g. fixed swing box with ≥2 confirmed touches), not more gates on rolling Donchian.
- LIVE: **no**.
