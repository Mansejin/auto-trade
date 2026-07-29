# LIVE month review — 2026-07

Generated: 2026-07-29T09:24:06Z  
Policy tag: `None`

## Current snapshot
- regime: `None`
- selected: `None`
- sideways_dwell / gate: `None` / `None`

## Regime-switch log (2026-07)
- rows: 0
- actions: `{}`
- regimes: `{}`
- switches: 0 (to Williams: 0, to v5 fallback: 0)
- premium-watcher rows: 0

## Suggestion (ops only)
- **keep** — Insufficient evidence to change Policy C map

## Rules
- Allowed: keep, demote_sideways_to_v5, raise_dwell_to_14, ops_check, inconclusive
- Forbidden: retune Williams WR/ADX thresholds from this month alone; auto-deploy without human

## Human PnL input (optional next run)
```bash
MONTHLY_LIVE_PNL_PCT=-2.5 MONTHLY_LIVE_TRADES=10 python3 scripts/monthly_live_review.py --month 2026-07
```

Do not auto-deploy from this report.
