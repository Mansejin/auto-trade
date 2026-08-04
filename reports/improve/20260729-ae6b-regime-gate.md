# AE6b — Regime-gated flush-fade (no param retune)

> Same JSON as AE6: `strategies/alpha-ae6-mfi-wr-flush-fade-4h.json`  
> **No** MFI/WR/ADX/SL/TP changes (anti-overfit).  
> Only question: does restricting evaluation to daily **bear/sideways** segments rescue the edge?

## Hypothesis

AE6 flush-fade has positive expectancy **when limited to** regime-engine-v2 `bear` + `sideways` segments (vs always-on, which was falsified).

## Falsification (pre-registered)

1. Among bear/sideways segments with **n ≥ 3**, fewer than half have `ret > 0` **and** `PF ≥ 1`, **or**
2. Signal remains too sparse for a specialist (majority of segments have n ≤ 1), **or**
3. A deep-bear segment with n ≥ 3 has PF < 0.5 (gate does not protect the worst dumps).

Bull segments are **controls only** (expect weak/negative if gating thesis is right).

## Segment results (toolkit stdout)

Source labels: `reports/regimes-krw-btc-1d-v2.json`  
Raw log: `reports/improve/ae6b-segment-runs.jsonl`

| Regime | Window | Ret | B&H | PF | n |
|--------|--------|----:|----:|---:|--:|
| sideways | 2024-01-04→02-11 | +0.37% | +11.97% | ∞ | 1 |
| bear | 2024-08-09→10-03 | +0.15% | −4.04% | ∞ | 1 |
| sideways | 2024-10-04→10-17 | 0.00% | +11.21% | — | 0 |
| sideways | 2025-01-07→02-05 | 0.00% | +2.95% | — | 0 |
| bear | 2025-11-27→2026-01-03 | **+6.62%** | −4.04% | **3.20** | 3 |
| bear | 2026-01-20→03-23 | **−5.40%** | −25.40% | **0.13** | 3 |
| sideways | 2026-03-24→04-21 | +1.19% | +6.50% | ∞ | 1 |
| bear | 2026-05-26→07-27 | +1.62% | −16.56% | 1.64 | 3 |
| bull (ctrl) | 2025-07-12→11-03 | −2.87% | +1.60% | 0.43 | 5 |
| bull (ctrl) | 2023-10-31→2024-01-03 | +1.43% | +29.88% | ∞ | 1 |

## Verdict

**FALSIFIED for promotion / Policy overlay.**

- Only **3** bear/sideways segments have n ≥ 3; **5/8** target segments have n ≤ 1 → not a usable specialist.
- Deep-bear `2026-01-20→03-23`: PF **0.13**, ret −5.40% → gating does **not** stop the bad dump trades.
- Bull control `2025-07→11` loses (PF 0.43) — gating *direction* looks right, but AE6 itself is too sparse/fragile to ship.
- Early (pre-2026) bear/sideways compound ≈ **+0.5%** over 4 segments — noise, not alpha.

**Do not** loosen MFI/WR thresholds to raise trade count.

## Next

- Close AE6/AE6b flush-fade line for LIVE/Policy C.
- **AE7**: one alt-data hypothesis with an event study (no Strategy JSON retune). Prefer Binance funding extremes → KRW-BTC forward return, with a frozen holdout.
