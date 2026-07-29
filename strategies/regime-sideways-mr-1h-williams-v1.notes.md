# Regime Sideways MR 1h Williams %R v1

## Hypothesis
ADX가 약한 횡보에서 Williams %R &lt; -80 과매도는 단기 평균회귀가 자주 발생한다. ADX≥25가 되면 MR을 종료하고 추세 레짐으로 넘긴다.

## Frozen rules
- Buy: ADX(14)&lt;20 AND Williams%R(14)&lt;-80
- Sell: Williams%R&gt;-20 OR close≥BB middle OR ADX≥25
- SL −2% / TP +3%
- TF: 1h KRW-BTC

## Mount contract (critical)
**Only while daily regime == sideways** (Policy C engine).

Paper / research mount modes (`scripts/williams_dwell_gate.py`):
- **`dwell7` (preferred develop)** — allow when sideways dwell >= 7
- `dwell14` — stricter; blocks stubs but regressed old1 in BT
- `hybrid` — dwell 7..13 early-strict v2; dwell>=14 base v1 (mixed; not preferred)

See `reports/improve/20260729-williams-dwell-develop.md`.

1h ADX<20 alone is NOT enough — on 2026-04-28~07-28 mixed bear the same JSON lost -20.8% (PF 0.28).

## Sideways-window results (daily ADX&lt;20 stretches)
| Window | Trades | WR | PF | Return | Bench |
|---|---|---|---|---|---|
| 2025-06-05~07-13 | 12 | 75% | 1.85 | +0.58% | +9.89% |
| 2025-08-20~10-02 | 24 | 79% | 1.53 | +0.61% | +5.68% |
| 2026-03-24~04-22 | 9 | 78% | 1.51 | +0.54% | +7.14% |
| 2025-08-05~08-15 (extra) | 6 | 100% | ∞ | +1.57% | +2.78% |

## Verdict
- **Research retain** as `sideways` **candidate** (orthogonal shelf)
- **Not promote** to LIVE / Policy C map yet (needs strategy_audit + human approve; still trails buy&hold in sideways)
- Do not run always-on without daily regime switcher

## Falsification (if promoted later)
- PF&lt;1 on ≥2 of 3 primary SW windows
- Or regime-mounted forward paper month with PF&lt;1
