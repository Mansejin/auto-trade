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
- **AE6** MFI+Williams flush-fade: **falsified** as standalone alpha — see `reports/improve/20260729-ae6-flush-fade.md`
- **AE6b** regime-gated AE6: **falsified** (sparse + deep-bear PF 0.13) — `reports/improve/20260729-ae6b-regime-gate.md`
- **AE7/AE7b** funding extremes: AE7 untestable at −0.05% in available history; AE7b relative 10th-pct **falsified** on holdout mean — `reports/improve/20260729-ae7*.md`
- **AE12** lag-MDD + forward collect: **done** — 7d risk-off median MDD −5.45% (material); collectors shipped
- **AE12b**: H1 RETAINED (HTX); H2 NOT_READY (OB collect) — `reports/improve/20260729-ae12b-event-study.md`
- **AE12c**: H1 fee stress **SURVIVES 20bps** (through 30; fails 50) — research only — `20260729-ae12c-fee-stress.md`
- **AE13**: Upbit internal premium — H_rich fade RETAINED; H_cheap FALSIFIED — `20260729-ae13-upbit-premium.md`
- **Next open:** AE14 — re-run H2 after OB collect; do not mine funding/premium cuts; no LIVE promote without audit
- Keep LIVE caps sized for lag worst-case; do not restart AE6–AE11 TA scrapes

## Local handoff

Cloud → local continuation brief + paste prompt: **`docs/handoff-alpha-local-agent.md`**

