# 나씨 3틱 B + TP 0.5% — 2026-07-29

Card: [`docs/research/nassi-3tick-b-tp05-card-frozen.md`](../../docs/research/nassi-3tick-b-tp05-card-frozen.md)

## Results vs B (0.1% reclaim)

| Window | B trades / net | TP05 trades / net | Verdict |
|--------|----------------|-------------------|---------|
| 2026-05 | 16 / **+0.10%** | 11 / **+0.13%** | pass (slight ↑) |
| 2026-06 | 35 / **+0.33%** | 1 / **−1.92%** | **fail** (28d bag, force_exit −15%) |
| 2026-07 | 10 / **+0.06%** | 7 / **+0.16%** | pass (slight ↑) |

**Not falsified** by ≥2/3 rule (1/3 fail), but **worse than B** on the stress month.

## Read

- Looser TP (0.5%) raises per-win avg (~0.58–0.61%) and can lift quiet months a little.
- Cost: fewer cycles; one June entry never reaches +0.5% and sits ~month → large force_exit loss. B’s **0.1% reclaim was the ruin cut**, not the bug.
- SL (−20%) still not the binding constraint here.
- **Do not retune.** Prefer B’s tight reclaim over this card. No LIVE.
