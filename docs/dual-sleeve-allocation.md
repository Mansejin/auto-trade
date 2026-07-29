# Dual-sleeve capital allocation (CORE + SCALP)

> Intent: **split capital**, not replace Policy C.  
> Config source of truth: [`config/sleeves.json`](../config/sleeves.json)

## Why

One Upbit bot can only run one `STRATEGY_PATH`. Mixing swing (4h/1h) and scalps on the same wallet forces constant regime-file swaps and blocks shorts (Upbit spot).

Split (human-frozen **2026-07-29**: 장기 7 / 단타 3):

| Sleeve | 한글 | Venue | Role | Capital |
|--------|------|-------|------|---------|
| **CORE** | 장기 | Upbit spot (`upbit-paper-bot`) | Policy C swing / MR | **70%** |
| **SCALP** | 단타 | Bitget UTA futures (Freqtrade) | Short-capable, faster TF | **30%** |

Do not auto-tune weights from one month of live PnL.

```mermaid
flowchart LR
  Capital --> CORE["장기 CORE 70% Upbit"]
  Capital --> SCALP["단타 SCALP 30% Bitget"]
  CORE --> PC["Policy C map"]
  PC --> Bull["bull 4h-v2"]
  PC --> Bear["bear m5-v6"]
  PC --> Side["sideways Williams 1h / v5 fallback"]
  SCALP --> BS["bear short scalp slot"]
  SCALP --> SS["sideways 15m scalp slot"]
  SCALP --> BuS["bull scalp slot empty"]
```

## Sideways separation (required)

| Sleeve | Strategy | Notes |
|--------|----------|-------|
| CORE | `regime-sideways-mr-1h-williams-v1` (dwell≥7) else `…-4h-v5` | Already LIVE. Treat as **swing MR**, not scalp. |
| SCALP | `SidewaysScalp15mBbV1` (research draft) | Independent Bitget long+short 15m BB fade. Validate before funding. |

Do **not** demote Williams to “make room” for a scalp — fund the scalp from the SCALP wallet instead.

## Bear separation

| Sleeve | Strategy | Status |
|--------|----------|--------|
| CORE | `m5-v6` long-biased 1h | LIVE — keep |
| SCALP | `BearShortBreakdownVolV6` (and prior v1–v5) | Research falsified so far — slot open |

## Ops rules

1. CORE and SCALP never share a position book.
2. Promoting a scalp never edits `POLICY` in `remote_regime_switch.py` unless you explicitly want CORE changed.
3. Premium / kimchi overlay stays on CORE until SCALP has its own contract.
4. Empty scalp slots → that % stays in cash / idle wallet (do not fold into CORE silently without a decision).

## Status helper

```bash
python scripts/sleeve_status.py
```

## Related research

- Bear short hunt: `reports/improve/20260729-bear-short-scalp.md`
- Williams LIVE promote: `reports/improve/20260729-williams-live-promote.md`
