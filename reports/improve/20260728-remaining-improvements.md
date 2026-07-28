# Remaining Improvements Progress — 2026-07-28

## Done this pass

| Area | Action | Result |
|------|--------|--------|
| Regime auto-switch | Server cron + `remote_regime_switch.py` | **Already live** (daily 15:20 UTC) |
| Bull participation | Extra sweep vs bull-v2 | **No better candidate** under stability constraints → keep `regime-bull-trend-4h-v2` |
| Sideways stability | Segment compound sweep | Promoted **`regime-sideways-mr-4h-v5`** (comp ~+37.2 vs v4 ~+34.5 on sideways set) |
| Bear balance | Audit-like re-sweep around v6 | **No superior alt** → keep LIVE `m5-v6` |
| LIVE risk | Caps on remote `.env` | `MAX_ORDER_KRW=15000`, `MAX_DAILY_LOSS_KRW=5000` |
| Walk-forward ops | `scripts/walk_forward_check.py` | Diagnostic tool added |

## Policy C 5y compound (segment chain)

| Map | Compound | B&H chain |
|-----|----------:|----------:|
| bull-v2 + sideways-v4 + bear-v6 | +415.41% | +87.46% |
| bull-v2 + **sideways-v5** + bear-v6 | **+425.85%** | +87.46% |

## Still open / next

1. **Cursor Automations monthly job** — paste `docs/monthly-automation-prompt.md` in dashboard (human one-time setup).
2. **Bull late-entry problem** — 2021-10 still lags B&H; needs different family (not just EMA tweaks) or accept participation gap.
3. **Position / desk UX** — optional: surface current regime on desk UI (`upbit-desk`).
4. Re-run `walk_forward_check.py` after each monthly candidate.

## LIVE snapshot after changes

- Regime: bear → `m5-v6`
- Order cap: 15,000 KRW / daily loss brake: 5,000 KRW
- Sideways file ready on server for next sideways flip: `regime-sideways-mr-4h-v5.json`
