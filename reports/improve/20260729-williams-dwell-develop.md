# Williams develop — dwell7 vs dwell14 vs hybrid

Date: 2026-07-29  
Base: `regime-sideways-mr-1h-williams-v1` (WR<-80, ADX<20) — thresholds frozen  
Early-strict: `regime-sideways-mr-1h-williams-early-strict-v2` (WR<-80, **ADX<15**) — only for hybrid early band  
Helper: `scripts/williams_dwell_gate.py`

## Fail-case targets
| Case | Ungated | Wanted |
|---|---|---|
| Apr-2025 SW-new2 | -1.38% PF0.61 | mitigate |
| Jul-2026 SW-new3 | -4.07% PF0.03 | block |

## A) dwell >= 7 (base Williams only)

| Tag | Gated window | Return | PF | Trades | WR | Notes |
|---|---|---|---|---|---|---|
| SW-new1 | 02-04~02-06 | +0.84% | 9.97 | 3 | 67% | short allow-tail |
| SW-new2 | 04-10~04-25 | **+0.37%** | inf | 4 | 100% | **Apr fail fixed** |
| SW-old1 | 06-11~07-13 | -0.27% | **1.35** | 10 | 70% | better than dwell14 |
| SW-A | 08-11~08-15 | +0.20% | inf | 1 | 100% | sparse |
| SW-old2 | 08-26~10-02 | +0.20% | 1.62 | 21 | 81% | pass |
| SW-B | 01-04~01-05 | 0% | N/A | 0 | — | no fill |
| SW-old3 | 03-30~04-22 | **+1.30%** | **2.20** | 6 | 83% | best of old3 variants |
| SW-new3 | — | — | — | — | — | **FILTERED** (Jul stub) |

## B) dwell >= 14 (reference, prior run)

| Tag | Gated | Return | PF | Trades |
|---|---|---|---|---|
| SW-new2 | 04-17~04-25 | +0.24% | inf | 2 |
| SW-old1 | 06-18~07-13 | **-0.96%** | **0.87** | 7 |
| SW-old2 | 09-02~10-02 | +0.17% | 1.99 | 15 |
| SW-old3 | 04-06~04-22 | +0.42% | inf | 1 |
| new1/A/B/new3 | — | FILTERED | | |

## C) hybrid (early dwell7-13 = early-strict ADX<15; mature >=14 = base)

| Tag | Early (7-13) | Mature (>=14) |
|---|---|---|
| SW-new1 | +0.84% n=3 PF9.97 | FILTERED |
| SW-new2 | 0 trades | +0.24% n=2 |
| SW-old1 | **+0.66% n=2** | -0.96% PF0.87 |
| SW-A | +0.20% n=1 | FILTERED |
| SW-old2 | **-1.73% PF0.28 n=3** | +0.17% PF1.99 |
| SW-B | 0 trades | FILTERED |
| SW-old3 | +0.61% n=1 | +0.42% n=1 |
| SW-new3 | FILTERED | FILTERED |

Hybrid helps old1 early segment but **old2 early is bad**; mature old1 still fails. Not cleaner than dwell7 alone.

## Develop verdict
**Prefer paper mode = `dwell7`** (base Williams, no early-strict):
1. Blocks Jul stub (new3)
2. Turns Apr-2025 into +0.37% / 4 wins
3. Avoids dwell14's old1 PF break (0.87); dwell7 keeps PF1.35
4. Lifts old3 to +1.30% PF2.20

Caveats: still often trails buy&hold; short tails (new1/SW-A) can still trade; not LIVE.

Recommended next: paper-log with `python scripts/williams_dwell_gate.py --mode dwell7` when regime engine says sideways.

LIVE / Policy C unchanged.
