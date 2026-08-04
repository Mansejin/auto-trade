# Policy C OOS presample (pre-2021 selection window)

> **Not investment advice.** Map frozen — no ADX/TF retune.

## Window

| | |
|--|--|
| Requested | 2017-09-01 → 2021-07-26 |
| Effective (after SMA200 warmup) | **2018-04-12 → 2021-07-24** |
| Segments | 25 / 25 OK |
| Map | bull/transition → `regime-bull-trend-4h-v2`; bear → `m5-v6`; sideways → `regime-sideways-mr-4h-v5` |

Artifact: `reports/bt-policyC-oos-presample-20260730_132503.json`  
Script: `scripts/bt_policyC_oos_presample.py`

## Result (aligned B&H)

| | Policy C | BTC hold (aligned) |
|--|--------:|-------------------:|
| Return | **+387.4%** | **+393.9%** |
| Multiple | 4.87× | 4.94× |
| MDD | **−36.7%** | −66.6% |
| Beats B&H return? | **No** (slightly under) | |
| Beats B&H MDD? | **Yes** | |

## Verdict

- **Return edge vs hold did NOT replicate** outside the 2021–2026 selection sample (near flat / slight underperform).
- **MDD edge DID replicate** (−37% vs −67%) — same character as in-sample continuous race.
- Supports: Policy C as a **risk-shaped** regime portfolio, not a guaranteed return multiplier.
- Weakens: treating the +426% fair-race multiple as portable alpha.

## Next (optional)

1. Fee/slippage stress on same OOS path  
2. Walk-forward: train map thresholds on half OOS, blind other half (heavier; only if human wants retune study — currently frozen map)
