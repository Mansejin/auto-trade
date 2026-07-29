# Hammer Reclaim Long — FROZEN

> 모토: [`docs/motto.md`](../motto.md) · 빗각 접음 · **되돌림** 가격행동

| Field | Value |
|-------|-------|
| Status | **FROZEN** 2026-07-29 |
| One-liner | 긴 아래꼬리 + 양봉이면 롱, 꼬리 저점 깨면 아웃 |
| Universe | BTC / ETH / SOL (USDT-perp), **24h** |
| TF | 15m |
| Side | Long only |
| Code | `HammerReclaimLongV1` |
| Hypers (≤3) | `wick_body_k=2.0` · `min_wick_frac=0.55` · `body_max_frac=0.35` |

Do **not** retune after fail. Revise card/hypothesis only.

---

## Rules

1. **Signal candle** (15m):
   - `close > open` (양봉)
   - `lower_wick ≥ wick_body_k × body`
   - `lower_wick ≥ min_wick_frac × (high−low)`
   - `body ≤ body_max_frac × (high−low)`
   - `lower_wick > upper_wick`
2. **Entry**: next bar open / signal close (freqtrade default: signal bar close).
3. **Stop**: absolute at signal candle `low` (custom stoploss). Hard floor −5% if data missing.
4. **Take profit**: ROI **1.0%** backup (not a 4th hyper; approximate fixed scalp). No indicator exits.
5. **Session**: none (24h).

---

## Falsify

≥2/3 independent ~30d windows on the multi-pair book: **PF < 1 or net < 0** → falsified.  
Per-pair notes for learning; decision on aggregate.

LIVE/SCALP: **no** until survive.

---

## Why this

User preference: 되돌림 / rejection wick.  
Simple, mechanical, no 빗각. Open universe per motto.
