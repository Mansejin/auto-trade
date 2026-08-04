# Regime Sideways MR 1h ADX-switch v1

## Hypothesis
1h에서 ADX가 약할 때(ADX&lt;20) RSI 과매도 + BB 하단 이탈은 평균회귀가 잘 되고, ADX가 강해지면(≥25) 추세가 시작되므로 MR을 끊고 추세 전략으로 넘겨야 한다.

## Rules (frozen)
| | |
|---|---|
| Buy | ADX(14)&lt;20 AND RSI(14)&lt;35 AND close ≤ BB lower(20,2) |
| Sell | RSI≥55 OR close ≥ BB middle OR **ADX≥25** (trend-on exit) |
| SL / TP | −2.0% / +3.0% |
| Market / TF | KRW-BTC / 1h |

## Switch contract (research candidate — not Policy C)
| Signal | Action |
|---|---|
| Daily/engine: ADX&lt;20 → `sideways` | Prefer this MR slug (candidate) |
| Daily/engine: ADX≥20 → bull/bear/transition | Prefer trend slug (existing Policy C map) |
| In-strategy: ADX≥25 while in MR position | Sell (hand off; do not ride MR into trend) |

**Do not** change LIVE `POLICY` / `STRATEGY_PATH` without audit + human approve. Current Policy C sideways remains `regime-sideways-mr-4h-v5`.

## Falsification
- Win rate &lt; 40% or PF &lt; 1.0 on default 1h period (last ~3 months)
- MDD &gt; 20%
- ADX≥25 exits dominate with net loss vs RSI/BB exits alone (switch exit adds no value)

## Orthogonal note
Distinct from 5m Bitget scalp research: this is Upbit 1h MR regime **candidate**, ADX-gated both at entry and as switch-exit.
