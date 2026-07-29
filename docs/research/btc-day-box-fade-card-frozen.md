# BTC Day-Box Fade CORE — FROZEN

> 모토: [`docs/motto.md`](../motto.md) · 나씨 접음 · **1일 박스 S/R 페이드**

| Field | Value |
|-------|-------|
| Status | **FROZEN** 2026-07-29 |
| One-liner | BTC 약 1일 박스 폭이 1~2%일 때 상·하단을 페이드, 추세·이탈 시 중단 |
| Universe | **BTC** USDT-perp, **24h** |
| TF | 15m |
| Side | Long + Short |
| Leverage | **5** |
| Code | `BtcDayBoxFadeV1` |
| Hypers (≤3) | `touch_frac=0.15` · `adx_max=25` · `sl_buf_frac=0.05` |

Do **not** retune after fail. Revise card only.

---

## Rules

1. **Box** (15m): `lookback=96` (~24h). `hh=max(high)`, `ll=min(low)`, `mid=(hh+ll)/2`, `width=(hh−ll)/mid`.
2. **Regime**: trade only if `0.01 ≤ width ≤ 0.02` **and** `ADX(14) < adx_max`.
3. **Long**: `close ≤ ll + touch_frac×(hh−ll)` in regime.
4. **Short**: `close ≥ hh − touch_frac×(hh−ll)` in regime.
5. **TP**: `custom_exit` at **box mid** (반대 벽 전 절반 회수). `use_exit_signal=True`.
6. **SL**: absolute beyond box by `sl_buf_frac×(hh−ll)` (custom). Hard floor −15% (lev PnL).
7. **Danger pause (v1 proxies)**: ADX≥adx_max or width∉[1%,2%] → no new entries. Break of box handled by SL.

**Out of scope (later cards):** RSI/MACD divergence, news/events calendar, hand-drawn trendlines, multi-day nested boxes.

---

## Falsify

≥2/3 independent ~30d windows: **PF < 1 or net < 0** → falsified.  
(0-loss PF display → use net.)

LIVE/SCALP: **no** until survive with non-trivial net.

---

## Why

User: day-scale 1–2% box, fade edges, stop when “dangerous”; S/R family; lev ~5.  
CORE encodes box + ADX pause only — divergence/events need separate cards.
