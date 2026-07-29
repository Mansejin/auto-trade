# 나씨 5분봉 3틱 롱 + 순환 DCA — FROZEN

> 모토: [`docs/motto.md`](../motto.md) · 주간동아 인터뷰 + 시청자 정리본 · BTC only

| Field | Value |
|-------|-------|
| Status | **FROZEN** 2026-07-29 |
| One-liner | 의미 있는 음봉 3연속 → 롱, 1/40 분할 물타기, 평단 회복 청산 |
| Universe | **BTC** USDT-perp, **24h** |
| TF | 5m |
| Side | **Long only** |
| Code | `NassiThreeTickLongDcaV1` |
| Hypers (≤3) | `body_k=1.5` · `add_step_pct=0.004` · `max_adds=5` |

Do **not** retune after fail. Revise card/hypothesis only.

Sources: [주간동아](https://weekly.donga.com/economy/article/all/11/2913751/1) · [정리본](https://shinboogie.tistory.com/52)

---

## Rules (mechanical)

1. **Tick (음봉)**: `close < open` and `|body| ≥ body_k × median(|body|, 20)`. Short/doji ticks do not count (break the run).
2. **Entry**: 3 consecutive ticks → long at 3rd close.
3. **Run floor**: 3-bar drop `(open[-2] − close[0]) / close ≥ 0.3%` (횡보 3틱 제외). Constant.
4. **Pump skip**: any green bar in last 6 with `body ≥ 3 × median` → no entry (장대양봉 직후). Constant.
5. **Stake**: each entry slice = **available stake / 40** (기사 초보 분할). Constant.
6. **DCA**: adverse from avg ≥ `add_step_pct × n_entries` → add one slice. Max extra = `max_adds`.
7. **Exit**: `custom_exit` when `current_profit ≥ 0.001` (`use_exit_signal=True`).
8. **Stop**: research hard floor **−20%** only (원본 손절 거의 없음의 blast radius).

**Out of scope (repute as new card if needed):** 15/30분 전환, 1분봉 저점 진입, 호가벽, 오전 9–10시, SMA 추세 재량, 찐바닥 “짧아지는 음봉” 추매 타이밍.

---

## Falsify

≥2/3 independent ~30d windows: **PF < 1 or net < 0** → falsified.  
(Ignore PF display `0.00` when zero losing trades; use net.)

LIVE/SCALP: **no** until survive.

---

## Relation

Prior fade±DCA cards falsified or mismatched source (both sides / absolute 0.15%). This card = article-faithful **long-only 3-tick + 1/40 DCA**.
