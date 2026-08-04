# mid-swing-4h-ema-adx-v1 — FALSIFIED

Shorter swing than Policy C (no daily regime). **Do not LIVE.**

## Frozen

| Field | Value |
|-------|--------|
| File | `strategies/mid-swing-4h-ema-adx-v1.json` |
| TF | 4h |
| Entry | EMA5×EMA20 cross_above + ADX&gt;23 + RSI&lt;60 |
| Exit | cross_below OR RSI&gt;70 |
| SL / TP | 4% / 12% |
| Script | `scripts/bt_mid_swing_4h_race.py` |
| Artifact | `reports/bt-mid-swing-4h-race-20260731_053636.json` |

## Result

| Window | mid-swing | always bull-v2 | B&H |
|--------|----------:|---------------:|----:|
| in-sample 21–26 | **−21.6%** / MDD −38% | +435% / −47% | +109% / −74% |
| OOS 18–21 | **−18.4%** / MDD −35% | +890% / −30% | +394% / −67% |

## Verdict

**FALSIFIED vs hold** on both windows. ADX/RSI + tight 4/12 SLTP underperforms plain bull-v2 (wide 10/40) and loses money while BTC rose.

Implication: “shorter swing with more filters” here just cut winners; Policy C / bull-v2 sleeve remains the swing stack. No knob shopping on this id.
