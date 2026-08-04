# 나씨 3-bar Fade CORE — FROZEN

> 모토: [`docs/motto.md`](../motto.md) · 되돌림 / 과열 페이드 · BTC only

| Field | Value |
|-------|-------|
| Status | **FROZEN** 2026-07-29 |
| One-liner | 5m 동일방향 긴 봉 3연속 → 반대 방향 단기 페이드 |
| Universe | **BTC** USDT-perp only, **24h** |
| TF | 5m |
| Side | Long + Short |
| Code | `NassiThreeBarFadeV1` |
| Hypers (≤3) | `body_k=1.5` · `min_body_pct=0.0015` · `body_lookback=20` |

Do **not** retune after fail. Revise card/hypothesis only.

---

## Source idea (discretionary)

나씨 “순환매매”: 5m 유의미한 긴 봉 3연속(양/음) 후 반대로 잡고 단기 반등. 더 가면 비중 추가(평단), 평단 회복 시 전량. 손절 거의 없음. BTC only. 목표 서술 “5~10%”는 레버리지/계좌 기준일 가능성 큼(스팟 5m 5%와 불일치).

---

## CORE encoding (this card)

**In scope**

1. **Long bar**: `|body| ≥ body_k × median(|body|, body_lookback)` **and** `|body|/close ≥ min_body_pct`.
2. **Bull run**: 3 consecutive long bars, all green (`close > open`) → **enter short**.
3. **Bear run**: 3 consecutive long bars, all red (`close < open`) → **enter long**.
4. **Entry**: signal on 3rd bar close (freqtrade default).
5. **Stop**: absolute at impulse extreme of the 3 bars (long: `min(low)`; short: `max(high)`). Hard floor −5%.
6. **Take profit**: ROI **0.5%** (price). Not a 4th hyper — fixed scalp proxy for “단기 기술적 반등”. Original “5–10%” not used as price TP.
7. **Session**: none (24h). Single position (`max_open_trades=1`).

**Out of scope (v1)**

- 물타기 / 평단 순환 / 무손절 — capital-structure, not edge. Do not encode until CORE fades survive.

---

## Falsify

≥2/3 independent ~30d windows (BTC only): **PF < 1 or net < 0** → falsified.

LIVE/SCALP: **no** until survive.

---

## Why this

User idea family: fade after consecutive impulse bars. Motto path: freeze ≤3 hypers, single entry + defined risk, falsify before any martingale layer.
