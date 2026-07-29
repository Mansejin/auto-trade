# 나씨 3-bar Fade + DCA V1 — 2026-07-29

Card: [`docs/research/nassi-3bar-fade-dca-card-frozen.md`](../../docs/research/nassi-3bar-fade-dca-card-frozen.md)

Hypothesis: BTC 5m 3× relative-long same-color run → fade, DCA on adverse steps, exit at avg reclaim — has edge with hard −20% floor.

## Spec

| Item | Value |
|------|-------|
| Pair | BTC USDT-perp |
| Strategy | `NassiThreeBarFadeDcaV1` |
| Config | `config.bitget-nassi-3bar-fade-dca.json` |
| Hypers | `body_k=1.5` · `add_step_pct=0.004` · `max_adds=2` (**frozen**) |
| Exit | `avg_reclaim` @ +0.1% · floor SL −20% |
| Fee | 0.06% |

## v1 trade-count note

CORE v1 sparse trades were **real**: May filter signals ≈16 = May fills. Absolute `min_body_pct=0.15%` on each bar was over-strict (5m median body ≈0.04–0.07%). This DCA card uses relative `body_k` only.

## Results (~30d, BTC)

| Window | Trades | Profit % | PF | Market | Exit mix | Verdict |
|--------|--------|----------|-----|--------|----------|---------|
| 2026-05 | 19 | **+2.27%** | 2.52 | −3.4% | 18 avg_reclaim / 1 force_exit | pass |
| 2026-06 | 7 | **−18.04%** | 0.09 | −18.0% | 6 avg_reclaim / 1 **stop_loss −20%** | **fail** |
| 2026-07 | 2 | **−8.56%** | 0.02 | +9.0% | 1 avg_reclaim / 1 force_exit −8.9% | **fail** |

**Falsified** (2/3). High win-rate reclaim scalps do not offset the rare trend run that sits through max DCA then hits the floor (Jun) or ends the window still underwater (Jul).

## Read

- 물타기 인코딩은 동작함 (May: 18× avg_reclaim).
- Edge claim fails: one −20% wipe ≈ many small reclaim wins.
- **Do not retune** hypers. **Do not** remove the −20% floor to “match 손절 없음” without a new card (that only hides ruin).
- LIVE/SCALP: **no**.
