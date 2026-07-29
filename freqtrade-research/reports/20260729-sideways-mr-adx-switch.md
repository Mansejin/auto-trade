# Sideways MR + ADX switch candidate

Date: 2026-07-29

## Artifacts
| Layer | Path | Role |
|---|---|---|
| Upbit candidate | `strategies/regime-sideways-mr-1h-adx-switch-v1.json` | Policy C **alt** only (not LIVE map) |
| Notes / switch contract | `strategies/regime-sideways-mr-1h-adx-switch-v1.notes.md` | ADX&lt;20 enter, ADX≥25 exit→hand-off |
| Bitget FT | `freqtrade-research/.../SidewaysMrAdxSwitchV1.py` | 1h long+short MR + ADX switch |
| Registry | `regime-engine.json` → `sideways_adx_switch_v1_candidate` | listed; **policyC sideways unchanged** (still v5) |

## Switch logic
```
ADX < 20  → MR mode (allow entries)
ADX ≥ 25  → exit MR + no new MR (hand off to trend regime strategy)
20–25     → hysteresis band (no new entry if using daily engine ADX≥20; in-strat hold until 25)
```

## Smoke backtests (research, not promote)

### Upbit toolkit KRW-BTC 1h (2026-04-28 ~ 07-28)
- Trades 16 / WR 44% / PF **0.46** / Return **-6.30%** / Bench -19.49% / MDD -6.88%
- SL 3 / TP 0 / sell 12 / final_bar 1
- vs falsification (WR&lt;40 or PF&lt;1): **PF falsified** on this window

### Freqtrade Bitget BTC/USDT:USDT 1h (same span, fee 0.06%)
- Trades 17 / L12 S5 / PF **0.57** / Return **-4.43%** / Bench -17.33% / DD 4.94%
- Also PF &lt; 1 on this bearish sample

## Status
- **Candidate created** for regime switch shelf
- **Not promoted** to Policy C / LIVE
- Next (optional): sideways-only calendar windows (ADX&lt;20 days) rather than full 3m bear mix; do not retune thresholds on this fail
