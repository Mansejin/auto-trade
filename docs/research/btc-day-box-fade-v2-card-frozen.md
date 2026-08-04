# BTC Day-Box Fade V2 (anti-scrape) — FROZEN

> Parent: [`btc-day-box-fade-card-frozen.md`](btc-day-box-fade-card-frozen.md) · V1 기각(긁힘/스탑)

| Field | Value |
|-------|-------|
| Status | **FROZEN** 2026-07-29 |
| One-liner | 1–2% 일박스에서 **리젝션 윅으로만** 페이드, 박스 안정·쿨다운으로 연속 긁힘 차단 |
| Universe | BTC USDT-perp, 24h |
| TF | 15m |
| Lev | 5 |
| Code | `BtcDayBoxFadeV2` |
| Hypers (≤3) | `touch_frac=0.15` · `wick_body_k=1.5` · `adx_max=25` |

Do **not** retune. V1 hypers not carried as knobs.

---

## Delta vs V1 (why stops fired)

V1 entered whenever `close` sat in the edge band → false breaks scraped SL just outside the rolling box.

**V2 entry gates (all required):**

1. Same regime: `0.01 ≤ width ≤ 0.02`, `ADX < adx_max`, lookback=96.
2. **Stable box**: `|width − width.shift(16)| / width ≤ 0.25` (4h 폭 급변 = 이탈 위험 → 스킵).
3. **Edge tag + reclaim**: bar `low` (long) / `high` (short) enters edge band, but **close** is back toward mid (not closing through the wall).
4. **Rejection wick**: long → `lower_wick ≥ wick_body_k × body` and `close > open`; short → mirror.
5. **Cooldownoldown**: after any exit, no new entry for **6** bars (constant).

TP: box mid.  
**SL: signal rejection candle extreme** (`low` long / `high` short) — not beyond rolling box (V1 scrape source). Floor −15% lev.

---

## Falsify

≥2/3 ~30d: **PF < 1 or net < 0** → falsified.
