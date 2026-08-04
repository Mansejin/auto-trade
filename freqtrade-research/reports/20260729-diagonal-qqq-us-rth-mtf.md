# QQQ US-RTH Multi-TF Mode A — 2026-07-29

Port of `DiagonalUsRthMultiTfV1` from BTC → **QQQ/USDT:USDT** (Bitget stock perp).

Hypothesis: Nasdaq product during US RTH fits Inbum-style better than BTC;
same 4h→15m Mode A should improve PF.

## Spec

| Item | Value |
|------|-------|
| Pair | `QQQ/USDT:USDT` |
| Strategy | `DiagonalUsRthMultiTfV1` (unchanged rules) |
| Config | `config.bitget-diagonal-qqq-us-rth-mtf.json` |
| Session | US RTH 09:30–16:00 America/New_York |
| Structure | 4h volume-pivot → 15m Mode A touch |
| Data | 15m from 2025-10-28; **1d empty** → day_liquid defaults True |
| Fee | 0.06% taker |

## Results (~30d)

| Window | Trades (avg/day) | Profit | PF | Market | Verdict |
|--------|------------------|--------|-----|--------|---------|
| 2026-05 | 3 (0.10) | −0.73% | 0.40 | +10.8% | **fail** |
| 2026-06 | 5 (0.17) | −1.45% | 0.40 | −2.0% | **fail** |
| 2026-07 | 2 (0.07) | −1.22% | 0.00 | −7.6% | **fail** |

**Falsified** (3/3). Frequency OK for “~1 / 2 days” intent; expectancy not.

## Read

- Asset swap **did not** rescue Mode A first-touch.
- QQQ moves more “US-session native” but rail-touch MR still loses under fees.
- Next: **keep QQQ + US RTH + 4h structure**, change entry to **Mode B** (breakout → 15m retest).
