# 나씨 5분봉 3틱 롱 + DCA V1 — 2026-07-29

Card: [`docs/research/nassi-3tick-long-dca-card-frozen.md`](../../docs/research/nassi-3tick-long-dca-card-frozen.md)

Hypothesis: Meaningful 5m red 3-tick → long, 1/40 slices + DCA, avg reclaim — edge on BTC.

## Spec

| Item | Value |
|------|-------|
| Pair | BTC USDT-perp |
| Strategy | `NassiThreeTickLongDcaV1` |
| Config | `config.bitget-nassi-3tick-long-dca.json` |
| Hypers | `body_k=1.5` · `add_step_pct=0.004` · `max_adds=5` (**frozen**) |
| Stake | proposed/40 per fill |
| Filters | run drop ≥0.3% · skip if big green in last 6 |
| Exit | avg_reclaim @ +0.1% · floor −20% |
| Fee | 0.06% |

## Results (~30d, BTC)

| Window | Trades | Profit % | PF | Market | Exit mix | Verdict |
|--------|--------|----------|-----|--------|----------|---------|
| 2026-05 | 21 | **+0.16%** | n/a (0 losses) | −3.4% | 21 avg_reclaim | pass |
| 2026-06 | 4 | **−2.41%** | 0.02 | −18.0% | 3 reclaim / 1 stop (~−19% trade) | **fail** |
| 2026-07 | 15 | **+0.08%** | 7.65 | +9.0% | 14 reclaim / 1 force_exit | pass |

**Not falsified** by card rule (only 1/3 fail). Failures needed ≥2/3.

## Read

- Encoding closer to article: long-only 3-tick, short ticks excluded via `body_k`, 1/40 sizing, DCA.
- Trade count sane (~0.5–0.7/day when not in a bag).
- Account impact is tiny on win months (+0.1% class) because slices are 1/40; June bag still prints a −20%-class trade PnL but limited wallet hit.
- **Not LIVE/SCALP.** Formal survive ≠ economic edge. Do **not** retune hypers. Next evidence = more OOS windows or a **new** card (session/15m regime), not knob shop.
