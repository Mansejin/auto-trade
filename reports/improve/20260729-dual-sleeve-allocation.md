# Dual-sleeve + scalp research notes — 2026-07-29

## Allocation

- Config: `config/sleeves.json` — **장기 70% / 단타 30%** (`ratio 7:3`, frozen human 2026-07-29)
- Docs: `docs/dual-sleeve-allocation.md`
- Helper: `python scripts/sleeve_status.py`
- LIVE Policy C **unchanged** (CORE / 장기 only)

## Sideways split

| Sleeve | Strategy | Status |
|--------|----------|--------|
| CORE | Williams 1h (+ v5 dwell fallback) | LIVE |
| SCALP | `SidewaysScalp15mBbV1` | **falsified** on sample windows |

Sideways SCALP BT (Bitget 15m, fee 0.06%):

| Window | Trades | PF | Return |
|--------|--------|-----|--------|
| 20250605–20250713 | 83 | 0.56 | −6.6% |
| 20250820–20251002 | 110 | 0.46 | −11.0% |
| 20260324–20260422 | 58 | 0.76 | −3.1% |

→ Do not fund SCALP sideways yet. CORE Williams stays.

## Bear SCALP (v6)

`BearShortBreakdownVolV6` falsified (see `20260729-bear-short-scalp.md`). CORE `m5-v6` stays.
