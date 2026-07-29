# 나씨 3-bar Fade + DCA (순환매매) — FROZEN

> 모토: [`docs/motto.md`](../motto.md) · 나씨 순환매매 본체 · BTC only

| Field | Value |
|-------|-------|
| Status | **FROZEN** 2026-07-29 |
| One-liner | 5m 동일색 상대적 긴 봉 3연속 → 반대 진입, 逆행 시 물타기, 평단 회복 시 전량 |
| Universe | **BTC** USDT-perp only, **24h** |
| TF | 5m |
| Side | Long + Short |
| Code | `NassiThreeBarFadeDcaV1` |
| Hypers (≤3) | `body_k=1.5` · `add_step_pct=0.004` · `max_adds=2` |

Do **not** retune after fail. Revise card/hypothesis only.

---

## Why v1 trades looked “too few”

Backtest was fine. May signals under v1 filter ≈ **16** = May trades.

| Filter | May count (≈) |
|--------|----------------|
| Any 3 same-color | ~2000 |
| Each bar ≥ 1.5× median body | ~102 |
| Each bar ≥ **0.15%** body (v1) | ~17 |
| v1 full (rel ∧ pct) | **16** |

BTC 5m median body ≈ **0.04–0.07%**. Requiring **every** bar ≥ 0.15% was over-strict vs “유의미하게 길게”.

This card drops absolute `min_body_pct`; keeps **relative** `body_k` only.

---

## Rules

1. **Long bar**: `|body| ≥ body_k × median(|body|, 20)`.
2. **Bull run** 3 long green → **enter short**. **Bear run** 3 long red → **enter long**.
3. **DCA**: while open, if adverse from **current avg** ≥ `add_step_pct × n_entries`, add **equal stake** (same as first slice). Max extra fills = `max_adds` (total entries ≤ 1+max_adds).
4. **Exit**: `custom_exit` when `current_profit ≥ 0.001` (평단+수수료 버퍼). Requires `use_exit_signal=True` (freqtrade only calls `custom_exit` in that branch). Exit-trend always 0. No ROI ladder.
5. **Stop**: research hard floor only **−20%** (원본 “손절 거의 없음”의 blast-radius 천장). Not a hyper.
6. **Session**: 24h. `max_open_trades=1`.

---

## Falsify

≥2/3 independent ~30d windows: **PF < 1 or net < 0** → falsified.

LIVE/SCALP: **no** until survive. DCA path can look fine until a trend run hits the −20% floor — report that explicitly.

---

## Relation to CORE v1

[`nassi-3bar-fade-card-frozen.md`](nassi-3bar-fade-card-frozen.md) = single-entry, defined SL @ impulse — **falsified**.  
This card = user-stated 순환매매 (물타기 필수). New hypothesis, not a hyper retune.
