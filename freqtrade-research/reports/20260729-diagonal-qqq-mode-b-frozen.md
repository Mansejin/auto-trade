# QQQ Mode B Frozen V1 — 2026-07-29

Card: [`docs/research/mode-b-rule-card-frozen.md`](../../docs/research/mode-b-rule-card-frozen.md)

Hypothesis: Simple continuation Mode B (4h break → 15m retest+reject, US RTH, vol_k=1.5) has edge on QQQ under 0.06% fees.

## Spec

| Item | Value |
|------|-------|
| Pair | `QQQ/USDT:USDT` |
| Strategy | `DiagonalQqqModeBFrozenV1` |
| Config | `config.bitget-diagonal-qqq-mode-b-frozen.json` |
| Hypers | `vol_k=1.5`, `retest_bars=96`, `max_slope_pct=0.015` (**frozen**) |
| Exit | ROI 1.0% / SL −0.8% (no mid-exit) |
| Fee | 0.06% |

## Results (~30d)

| Window | Trades (avg/day) | Profit % | PF | Market | Verdict |
|--------|------------------|----------|-----|--------|---------|
| 2026-05 | 1 (0.03) | **+0.99%** | n/a (1 win) | +10.8% | pass (net) |
| 2026-06 | 1 (0.03) | **−0.91%** | 0.00 | −2.0% | **fail** |
| 2026-07 | 5 (0.18) | **−2.64%** | 0.27 | −7.4% | **fail** |

**Falsified** (≥2/3: net&lt;0 and/or PF&lt;1). Sparse as intended; expectancy not.

## Read

- Encoding matched the card (rejection, no mid-exit, vol 1.5). Still no edge in these windows.
- **Do not retune** `vol_k` / `retest_bars` / `max_slope_pct`.
- Next (if any): revise **card/hypothesis** (e.g. long-only with HTF bias, or different invalidate exit) — not knob search.
- LIVE/SCALP: **no**.

## Limits

Futures backtest; funding history incomplete for QQQ; 1d liq gate weak; slippage/book not modeled.
