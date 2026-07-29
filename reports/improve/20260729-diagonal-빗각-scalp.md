# 빗각(대각 채널) 단타 research — 2026-07-29

User style: discretionary **빗각 매매** (angled / fib-channel style) on short TF.
Encoded as linear-regression channel touch / break-retest on Bitget ETH 5m–15m.

## Why discretionary scalpers “can” and bots often can’t

1. **Skip filter**: humans discard ugly angles / news / thin books; bots take every rule match.
2. **Maker / queue**: live limit fills ≈ 0.02% vs backtest taker 0.06%×2.
3. **Path-dependent drawing**: hand-drawn 빗각 uses specific swing pivots; LR(40) is only a proxy.
4. **One bad scalp** is skipped by intuition; automated series pays every SL.

## Frozen rules

| Ver | Idea | Exit |
|-----|------|------|
| v1 | LR slope sign + reject at ±2σ rail (5m) | ROI 0.50% / SL 0.25% + mid |
| v2 | Failed break then retest of rail (5m) | ROI 0.60% / SL 0.30% + mid |
| v3 | Same as v1 on 15m | ROI 0.80% / SL 0.40% + mid |

Fee baseline: 0.06% taker. Maker stress: 0.02% on v1 W3 only.

## Results (ETH/USDT:USDT)

| Ver | W1 Nov–Dec | W2 Jan–Mar | W3 May–Jul | Verdict |
|-----|------------|------------|------------|---------|
| v1 5m | 36 / PF0.18 / −8% | 38 / 0.24 / −8% | 51 / 0.51 / −5% | **falsified** |
| v2 retest | 140 / 0.44 / −17% | 139 / 0.52 / −15% | 135 / 0.48 / −14% | **falsified** |
| v3 15m | 12 / 0.76 / −0.7% | 10 / 0.27 / −3% | 5 / 1.75 / +0.8% | **falsified** (2/3) |
| v1 maker 0.02% W3 | — | — | 51 / 0.89 / −0.8% | still &lt;1 (fee helps, no edge) |

## Takeaway

Short-TF 빗각 **as encoded** does not produce positive expectancy under multi-window falsification.
Maker fees improve the number but do not create an edge.
Keep SCALP capital cash; CORE Policy C unchanged.

## Next (needs human input — not threshold retune)

- User-specified pivot rules for drawing 빗각 (which swing highs/lows)
- Or hybrid: bot only alerts 빗각 touches; human confirms (not auto-order)
- Or leave short-TF scalp and fund CORE swing only
