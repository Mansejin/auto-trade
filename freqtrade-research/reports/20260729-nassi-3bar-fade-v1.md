# 나씨 3-bar Fade CORE V1 — 2026-07-29

Card: [`docs/research/nassi-3bar-fade-card-frozen.md`](../../docs/research/nassi-3bar-fade-card-frozen.md)

Hypothesis: After three consecutive “long” same-color 5m BTC bars, fading the opposite way (SL at impulse extreme, ROI 0.5%) has edge. Averaging / no-stop out of scope.

## Spec

| Item | Value |
|------|-------|
| Pair | BTC USDT-perp |
| Strategy | `NassiThreeBarFadeV1` |
| Config | `config.bitget-nassi-3bar-fade.json` |
| Hypers | `body_k=1.5` · `min_body_pct=0.0015` · `body_lookback=20` (**frozen**) |
| Exit | custom SL @ 3-bar extreme · ROI 0.5% |
| Fee | 0.06% |

## Results (~30d, BTC)

| Window | Trades (avg/day) | Profit % | PF | Market | Verdict |
|--------|------------------|----------|-----|--------|---------|
| 2026-05 | 16 (0.53) | **−1.44%** | 0.40 | −3.4% | **fail** |
| 2026-06 | 29 (1.04) | **−2.39%** | 0.55 | −18.0% | **fail** |
| 2026-07 | 16 (0.57) | **−1.66%** | 0.37 | +9.0% | **fail** |

**Falsified** (3/3). Sparse but consistently negative expectancy; many losers exit almost immediately (impulse continues through stop).

## Read

- Idea family (fade after consecutive long bars) still matches preference — **this CORE encoding** does not show edge on BTC 5m with defined risk.
- **Do not retune** the three hypers.
- **Do not** add 물타기 / 무손절 on a falsified CORE — that only changes capital path, not the signal edge.
- Card revision candidates (new card, not knobs): stricter “long” (higher `body_k` as **new** card only if re-hypothesized), 15m/1h instead of 5m, require run after quiet regime, or fade only into prior structure.
- LIVE/SCALP: **no**.
