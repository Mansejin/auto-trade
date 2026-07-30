# Regime daytrade-edge pack (frozen)

> Research decision 2026-07-30. **Not a Policy C / LIVE promote.**  
> Policy C map stays as in `docs/regime-auto-switch-playbook.md` until walk-forward + audit + explicit approve.

## Map (research)

| Regime | Card | TF | Role |
|--------|------|-----|------|
| **bull** | `strategies/regime-bull-trend-4h.json` | 4h | EMA8/21 swing (bull-year ≈ +157% vs bench +130%) |
| **sideways** | `strategies/daytrade-edge-side-15m-bb-fade-v5.json` | 15m | ADX&lt;20 + RSI&lt;30 + BB lower → upper |
| **bear** | `strategies/daytrade-edge-10m-div-atr-v1.json` | 10m | Div @ BB lower + ATR rising → upper |

## Closed / do not resume

- Bull **10m/15m** pullback daytrade line (v1–v9): fee bleed or sparse; best survivor ~+1%/y — not worth daytrading vs 4h swing.
- `bull-swing-4h-ema21-reclaim-v1`: survives weak gate (+17%) but **dominated** by `regime-bull-trend-4h`.
- Side 10m v2: side-only +7%; bleeds bull/bear. Prefer **v5 15m** (side +6%, bear ~flat, bull still −6% → **must be off in bull**).

## Operating notes

1. Side card is regime-gated: never leave on in labeled bull.
2. Bear daytrade and bull 4h swing are complementary; do not merge into one always-on card.
3. Promote to Policy C only after: multi-window re-check of this trio + `scripts/strategy_audit.py` (if used) + human OK.

## Windows used

- Bull: 2023-10-01 ~ 2024-10-01  
- Side: 2022-08-01 ~ 2023-08-01  
- Bear: 2025-07-29 ~ 2026-07-29  
