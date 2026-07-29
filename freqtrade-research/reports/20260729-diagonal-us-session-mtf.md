# 빗각 US session + Multi-TF — 2026-07-29

User constraints (new):
- ~1 trade / 2 days OK if volume is there
- Inbum-style: **only when US market is open**

## A) UsOpen (09:30–12:30 NY) — too tight

| Window (2w) | Trades | Profit | PF |
|-------------|--------|--------|-----|
| W1 May | 4 | −0.85% | 0.53 |
| W2 Jun | 0 | — | — |
| W3 Jul | 0 | — | — |

Code: `DiagonalUsOpenMultiTfV1.py` — **not useful** (no sample).

## B) UsRth (09:30–16:00 NY) — primary test

| Window (~30d) | Trades (avg/day) | Profit | PF | Market | Verdict |
|---------------|------------------|--------|-----|--------|---------|
| 2026-05 | 9 (0.30) | −2.30% | 0.46 | −3.4% | **fail** |
| 2026-06 | 1 (0.03) | −0.61% | 0.00 | −18% | **fail** |
| 2026-07 | 1 (0.04) | −0.61% | 0.00 | +8.6% | **fail** |

Code: `DiagonalUsRthMultiTfV1.py`  
Config: `config.bitget-diagonal-us-rth-mtf-v1.json`

**Falsified** (3/3). Frequency matches “rare” but expectancy does not.

## Read

- Session filter alone does not rescue **Mode A first-touch** on 4h rails.
- Jun/Jul almost never touched the 4h rail during RTH + vol filter.
- Locked-in product constraints going forward: **BTC, US RTH, multi-TF structure, low frequency OK**.

## Next (keep going — change entry logic, keep session)

1. **US-RTH + 4h Mode B** (breakout → 15m retest continuation) — different edge than touch-MR.
2. **US-RTH + 1h→15m Mode A** — more rail visits inside the same session box.
3. **US-RTH open auction only (first 90m) + Mode B** — closer to “열릴 때” literally, on continuation not MR.
