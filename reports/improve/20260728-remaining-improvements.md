# Remaining Improvements Progress — 2026-07-28 (pass 2)

## Done this pass

| Area | Action | Result |
|------|--------|--------|
| AE1 Monthly Automation | User confirmed enabled | **Done** |
| AE4 Bull non-EMA family | MACD/DI/Ichi/SMA/CCI/StochRSI/OBV vs bull-v2 | **No promote** — 5y Policy C compound still highest with bull-v2 (+425.85%). 2021-10 can be patched locally (SMA10/50 +33%) but Y4/compound lag. |
| AE5 Desk regime UX | `web/` in repo + ticker “레짐” + `logs/regime-current.json` | **Shipped** (server rebuild required) |

## Policy C 5y compound (unchanged map)

| Map | Compound | B&H chain |
|-----|----------:|----------:|
| bull-v2 + sideways-v5 + bear-v6 | **+425.85%** | +87.46% |

## LIVE snapshot

- Regime: bear → `m5-v6`
- Desk shows regime from `logs/regime-current.json` (fallback: last `regime-switch.jsonl`)
- Order cap: 15,000 KRW / daily loss brake: 5,000 KRW

## Open / later

- Accept 2021-10 participation gap under bull-v2, or explore **sub-regime** routing (not a single-engine swap)
- Monthly automation will re-check AE4-style candidates via `docs/monthly-automation-prompt.md`
