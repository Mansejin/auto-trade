# QQQ 4H 수동 채널 표본 — Batch 1 요약

| Field | Value |
|-------|-------|
| Updated | 2026-07-29 |
| Asset | Bitget `QQQUSDT` perp (USDT-FUTURES) |
| Structure TF | 4H |
| Window | 2026-04-19 → 2026-07-29 (~600 bars) |
| Log | [`channel-manual-sample-log.csv`](channel-manual-sample-log.csv) |
| Raw | [`data/qqq_usdt_4h.json`](data/qqq_usdt_4h.json) |
| Assist only | `_assist_channel_candidates.py` (후보 생성; 로그는 사람 검수) |

**n = 30** (게이트 최소치 도달). 전부 `hindsight=yes`.  
**ICT overlay (clearest 3)**: [`channel-clearest3-ict-overlay.md`](channel-clearest3-ict-overlay.md)  
**Edwards·Murphy 발췌**: [`edwards-murphy-excerpts.md`](edwards-murphy-excerpts.md)

---

## 사건 타입 분포

| event | n | 메모 |
|-------|---|------|
| B_break | 11 | 종가 이탈 |
| B_retest_ok | 7 | 리테스트 유지 |
| B_retest_fail | 1 | 가돌파/실패 이탈 |
| A_bounce | 9 | 경계 반등 |
| fakeout_or_chaos | 1 | 급락 구간 (06-09) |
| (기타 태그) | — | skip_reason에 steep/messy |

---

## 관찰 (코딩 규칙으로 굳히기 전)

1. **Mode B가 문헌과 가장 잘 맞음**  
    clearest wins: **S15→S16** (06-14 break → 06-15 retest → run), **S10→S11** (06-02), **S05** (약돌파+강 리테스트).

2. **리테스트 ≠ 자동 진입**  
   **S19**: 리테스트에 vol 폭발했지만 숏 방향으로 안 가고 반등. 거절 캔들/하위 TF 확인이 문헌의 “confirmation”에 해당.

3. **가파른 회복 채널은 조심**  
   **S13–S14** (06-09 이후): 돌파+리테스트는 됐지만 angle=steep → 고전 TA의 “권위↓”.

4. **Mode A는 단기 채널에서만 깨끗**  
   **S23** (07-21 lower bounce → upper) 후 **S24**로 하단 이탈. A로 먹고 C로 무효화 — 빈도↑하면 수수료에 녹기 쉬운 패턴(이전 봇 기각과 정합).

5. **거래량 없는 돌파**  
   **S04** (volx 0.86) vs **S05** 리테스트 volx 3.63 — 돌파봉보다 **리테스트/후속봉 vol**이 더 중요했던 사례.

6. **measured move**  
   **S11**: 폭 투영 목표 미달(조기 고점). MM을 고정 TP로 쓰기엔 표본 부족·미스 있음.

7. **Bitget QQQ 특수성**  
   주말·야간 봉 vol 극소. US cash RTH에 해당하는 봉만 쓰면 A/B 신호가 더 선명해질 가능성 → 다음 배치에서 `session=US_RTH` 컬럼 추가 검토.

---

## Mode B 최소 규칙 카드 (초안 → 고전 반영 개정)

상세 freeze 후보: [`edwards-murphy-excerpts.md`](edwards-murphy-excerpts.md) §6.

1. **구조**: 4H primary 2터치 + 3터치 확인 + parallel, steep 제외 (Edwards authority / Murphy).  
2. **돌파**: 종가 밖 + `vol ≥ 1.5×SMA20` — break는 heads-up (Murphy).  
3. **진입**: 리테스트에서 **거절 확인** 필수 (S19 / ICT sweep_reclaim). 거절 없는 고vol 터치 패스.  
4. **손절**: 리테스트 실패(종가 재진입).  
5. **목표**: 0.5×width → 1×width (S11 MM 올인 금지).

하이퍼 ≤3: `vol_k`, `retest_bars`, `max_slope`.

### Clearest 3 ICT 병기 요약

| Pair | 결과 |
|------|------|
| S15–16 | classic = ICT **동의** (gold) |
| S10–11 | 진입 동의, TP만 과욕 |
| S18–19 | classic 숏 오신호; ICT **sweep_reclaim** |

---

## 다음 배치

- [ ] CSV에 `session` 컬럼 (US RTH vs other)
- [ ] BTC 4H 보조 10건 (같은 규칙이 코인에서도 보이는지)
- [ ] Edwards–Magee / Murphy 발췌와 규칙 카드 대조
- [ ] TradingView에서 S15–S16, S10–S11, S19만 스크린/재작도 (hindsight 교차검증)
