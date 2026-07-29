# 추세선·평행채널 매매 — 문헌/자료 수집 노트

> **상태**: 자료수집 우선 (2026-07-29). **새 인코딩/백테스트 금지** until §8 체크리스트가 채워짐.  
> **한 줄**: “빗각”은 인범TV식 브랜드명에 가깝고, 본체는 고전 TA의 **trendline + parallel (price) channel** 이다.  
> 운영 스펙은 [`docs/inbum-diagonal-channel-playbook.md`](../inbum-diagonal-channel-playbook.md). 이 문서는 **근거·합의·미결**만 모은다.  
> **커뮤니티·ICT 심리 종합**: [`bitgak-community-psychology-synthesis.md`](bitgak-community-psychology-synthesis.md)

---

## 0. 왜 이 문서를 먼저 쓰나

지금까지의 실험(LR 프록시 → volume-pivot Mode A → MTF → US RTH → QQQ)은 **“빗각을 빨리 코딩”** 쪽에 기울었다.  
공개 자료를 다시 모으면:

1. 이름은 빗각이지만 **규칙은 채널 매매 교과서와 거의 동일**하다.
2. 유효한 전략으로 취급할 이유가 있다 — 수십 년 쓰인 S/R 기하 + 돌파·리테스트 심리.
3. 우리가 기각한 것은 “채널이 쓸모없다”가 아니라 **프록시·모드·빈도·세션을 잘못 인코딩한 것**일 가능성이 크다.

따라서 다음 단계는 파라미터 튜닝이 아니라 **문헌 합의 → 수동 차트 표본 → 그다음 최소 인코딩**.

---

## 1. 이름 정리 (온톨로지)

| 말 | 실제 의미 | 비고 |
|----|-----------|------|
| 빗각 (인범TV 등) | 기울어진 추세선 / 그걸로 만든 채널 | brunch @urbantrader: *“빗각 = 추세선, 활용 100% 동일”* |
| Trendline | 의미 있는 스윙 고/저를 이은 직선 | 2점 가설, 3점 확인 (StockCharts 등) |
| Parallel / price / trend channel | 추세선 + 평행 복사선 | ascending / descending / horizontal |
| Break + retest (throwback/pullback) | 돌파 후 옛 경계 재방문 | Mode B 핵심 |
| Measured move / channel width | 채널 폭을 돌파점에서 투영 | 목표가 관례 |
| Volume pivot / 거래량 터진 변곡 | 앵커 선택 휴리스틱 | 인범·투진사 쪽 강조점 (고전에도 vol 확인은 있음) |
| 고고저 / 저저고 | 채널 3점 작도 조합 | 평행채널 확정용 로컬 용어 |

**차별점 후보 (아직 검증 안 됨, 가설만)**

- 보조지표 최소 · 빗각만으로 대응 (시청자 관찰)
- **거래량 터진 자리**를 앵커로 고정 (매물대 심리)
- 미국장·나스닥처럼 “명확한 추세” 시장을 선호한다는 2차 진술 (brunch)
- Fib Channel 1:1 등으로 평행폭을 잡는 TV 관행 (커뮤니티)

→ “독창적 알파 인디케이터”가 아니라 **작도 취향 + 리테스트 규율** 쪽.

---

## 2. 출처 맵 (수집분)

### 2.1 고전 / 영문 표준

| 출처 | 요지 | URL |
|------|------|-----|
| Edwards & Magee, *Technical Analysis of Stock Trends* Ch.14–15 | Trendline / channel 권위, touch 횟수·기간·각도, penetration 후 pullback/throwback | 서적; 개요 https://www.edwards-magee.com/technical-analysis-how-to/ |
| StockCharts ChartSchool — Trend Lines | 2점 작도, **3번째 터치로 유효**, 가파른 각도는 신뢰↓ | https://chartschool.stockcharts.com/table-of-contents/chart-analysis/trend-lines.md |
| StockCharts Insider — Murphy Law #5 | 균등 간격·합리적 각도; **거래량 동반 이탈이 중요** | https://articles.stockcharts.com/article/stockcharts-insider-john-murphys-law-5-draw-the-line-trendlines/ |
| Investopedia — Price / Trading Channel, Channeling | 내부: 하단매수·상단매도; **돌파가 더 큰 기회**; confirmation = rebound 횟수 | https://www.investopedia.com/terms/p/price-channel.asp , `/terms/t/tradingchannel.asp`, `/trading/channeling-charting-path-to-success/` |
| Bulkowski — Throwbacks | 상방돌파 후 되돌림 통계·measure rule | https://thepatternsite.com/throwbacks.html |

### 2.2 현대 실전 가이드 (영문, 품질 편차 있음)

| 출처 | 요지 | URL |
|------|------|-----|
| GrandAlgo Parallel Channel | Bounce vs break+retest; 최소 2+1 touch; 폭 투영; 가운데 진입 금지 | https://grandalgo.com/blog/parallel-channel-trading-strategy |
| FinWiz Channel Trading | 3-touch, vol 1.5–2×, 종가 밖, 가돌파 후 복귀도 신호 | https://finwiz.io/technical-analysis/channel-trading |
| ChartMini / Proplynq 등 | Close rule, retest entry, SL just inside channel | chartmini / proplynq 블로그 |
| TradingView ideas (예: omar_elliot) | 상승채널 상단 돌파→리테스트 롱 등 도식 | TradingView ideas |

### 2.3 한국어 · 빗각/채널

| 출처 | 요지 | URL |
|------|------|-----|
| brunch @urbantrader /56 | **빗각≡추세선**; 돌파+리테스트 > 단순 터치; 보수 작도; 나스닥>코인 명확성 | https://brunch.co.kr/@urbantrader/56 |
| brunch @urbantrader /62 | 본질=**변곡점**; 추세=ABC; 되돌림(B)를 제대로 잡아야 선이 의미 있음 | https://brunch.co.kr/@urbantrader/62 |
| 투진사 프리미엄 | 인범 빗각=추세선; 고/저/고고저/저저고; 주→일→4h; vol 터진 자리=매물 | https://contents.premium.naver.com/tujunsa/bitcoin/contents/250901120032929yh |
| 시그비트 패러럴 채널 | 3-touch, 내부 vs 돌파+리테스트, vol로 진·가돌파, 미들라인 | https://sigbtc.pro/ko/community/education-board/post/6871 |
| 시그비트 추세선 | 피벗만 이을 것; 종가·vol·이탈폭 체크리스트 | https://sigbtc.pro/ko/community/education-board/post/3800 |
| EBC KR — Break & Retest | 추세선/채널도 동일 프레임 | https://www.ebc.com/kr/forex/270345.html |
| Phemex — 하락채널 돌파 | 종가+vol+리테스트; 하락채널에선 상단 숏도 | https://phemex.com/ko/academy/descending-channel-breakout-trading |
| jejuwind75 티스토리 | Bounce vs Break vs Fakeout; Al Brooks: 첫 돌파 가짜 많음 | https://jejuwind75.tistory.com/31 |
| Blind 스레드 | 인범 시청자: 피치포크 / Fib 채널 언급 | teamblind 포스트 |

### 2.4 아직 직접 못 연 것 (수집 백로그)

- [ ] Edwards & Magee Ch.14 원문 발췌 (penetration validity, channel value)
- [ ] John Murphy *Technical Analysis of the Financial Markets* trendline/channel 장
- [ ] Al Brooks price action — first breakout often fails (1차 소스)
- [ ] 인범TV 공개 클립/요약의 **앵커 선택·손절 틱·세션** (2차 노트만, 유료 복제 금지)
- [ ] Bulkowski pullbacks + channel patterns 통계 표
- [ ] 로그 vs 선형 채널 (BTC 장기) 실무 비교 글
- [ ] Pitchfork / Schiff vs parallel channel 경계

---

### 2.5 커뮤니티·ICT (심리 레이어)

상세: [`bitgak-community-psychology-synthesis.md`](bitgak-community-psychology-synthesis.md)

- Blind/디시: 주관 작도·기다림·도구 혼동(피치포크/Fib Channel)
- 한글 정리글: 빗각≡추세선으로 수렴
- ICT: **trendline liquidity** — 예쁜 다중터치 빗각 = 스탑 리본

---

## 3. 문헌 합의 (Consensus)

여러 출처가 같은 말을 반복하는 것만 “합의”로 적는다.

### 3.1 작도

1. **의미 있는 스윙**만 잇는다. 잡음 고/저 전부 연결 금지.
2. 상승: 저–저 (지지선) 먼저 → 고점에 평행. 하락: 고–고 먼저 → 저점에 평행.
3. **2점 = 가설, 3점(반대선 포함) = 확인**. touches↑ → 권위↑ (단, 과도한 테스트 후엔 깨질 위험도↑).
4. **각도**: 너무 가파르면(대략 60°+) 지속성↓. 너무 평평하면 약한 추세. “적당한” 각·간격.
5. **억지 평행 금지** → 쐐기/삼각은 별도 패턴.
6. **상위 TF 선이 하위보다 권위**. (주 > 일 > 4h)

### 3.2 매매 모드 (교과서 = 우리 Mode A/B/C)

| Mode | 합의 규칙 |
|------|-----------|
| **A 내부** | 추세 방향 경계에서만. 상승채널: 하단 롱 → 상단/미들 익절. **채널 한가운데 진입 금지**. SL은 경계 밖(또는 터치봉 극점 밖). |
| **B 돌파+리테스트** | **종가**로 이탈 확정 (윅만 X). **거래량↑**(관례 1.5–2×). 추격보다 **리테스트에서 역할 전환 확인 후** 진입. 목표가 ≈ **채널 폭 투영**. SL ≈ 채널 안 재진입. |
| **C 무효/가돌파** | 거래량 없는 돌파·재진입 = 실패돌파. 실패 후 반대 방향 매매도 문헌에 등장. |

### 3.3 거래량

- 경계 반등/이탈에 vol 동반 시 신뢰↑.
- 돌파 vol 부족 → 가짜 우선.
- (선택) 추세 진행 vol↑ / 되돌림 vol↓ = 건강한 채널.

### 3.4 목표·리스크

- 내부: 반대 경계 (또는 미들 부분청산).
- 돌파: **1× channel width** measured move가 가장 흔한 규칙.
- R:R는 경계에서 들어갈수록 유리 → 가운데는 구조적으로 불리.

### 3.5 시장·심리

- 채널은 **자기실현적 S/R** (많은 참가자가 같은 선을 봄).
- 첫 돌파는 가짜가 많다는 실전 쪽 경고(Brooks 계열) → **리테스트 대기**와 정합.
- 변동성·휩쏘 큰 시장(일부 코인)에서는 “명확한 추세”가 덜 나와 Mode B가 더 중요하다는 2차 진술.

---

## 4. 합의가 약한 / 출처마다 다른 점 (Disputed)

| 주제 | 입장들 | 우리 취급 |
|------|--------|-----------|
| 내부 Mode A 숏/롱 양방향 | Investopedia 등은 상단 숏도; 시그비트 등은 **추세 방향만** | 기본: 추세 순응만. 역추세는 별도 가설 |
| 돌파 직후 진입 vs 리테스트만 | 공격적 close-out / 보수적 retest | 문헌 다수·brunch = **리테스트 우선** |
| vol 배수 | 1.5× / 2× / “significantly higher” | 고정 숫자보다 **상대 폭증** 개념 유지 |
| 이탈폭 % | 시그비트 2–3% 등 | TF·자산 의존 → 절대값 조기 고정 금지 |
| Fib Channel / Pitchfork | 인범 시청자 툴 언급 | parallel과 **동일시하지 말 것** — 별도 조사 |
| 로그 스케일 | BTC 장기에 자주 권장 | 단기 데이/15m에는 비필수 가능 |
| 미들라인 | 시그비트 강조 / 고전은 부차 | 익절·필터 후보, 진입 필수 아님 |

---

## 5. 인범·빗각 특화로 남은 질문

문헌만으로는 **“인범만의 숫자 규칙”**이 없다. 남은 건 관찰·2차 요약:

1. 앵커를 **거래량 폭발 캔들**에 묶는 비중이 얼마나 큰가?
2. 미국장(RTH)만 보는가, 아니면 24h에서도 동일 작도인가?
3. 손절은 “종가 이탈”인가 “틱/윅”인가?
4. 하루 몇 타점·스킵 기준(얇은 날)의 실무 정의는?
5. Fib Channel을 parallel 대체로 쓰는가?

→ 이 답 없이 봇에 넣으면 **우리가 만든 규칙**이 되고, “빗각 검증”이 아니다.

---

## 6. 우리 실험과의 정합 (왜 기각이 문헌과 안 모순인가)

| 실험 | 문헌 대비 어긋남 |
|------|------------------|
| LR±2σ | 스윙·vol 앵커 아님. **회귀 밴드 ≠ 추세선 채널** |
| Mode A first-touch MR (15m/MTF/QQQ) | 합의는 “반등 **확인** + 가운데 금지”. 단순 터치·즉시 진입은 규율 약함. 수수료 하에서 얇은 edge |
| Human soft / pierce | 문헌의 핵심은 **종가 확정·vol·리테스트**, pierce 완화 아님 |
| US RTH 세션만 | 시장 선택은 문헌과 맞을 수 있으나, **Mode A 인코딩이 약하면** 세션만으로 안 산다 |
| Mode B 초안 | 문헌상 핵심 후보. 구현 중 mid-exit 충돌 등 **엔진 버그**가 먼저 — 전략 기각과 혼동 금지 |

**결론**: 채널 매매를 버린 게 아니라, **잘못된 프록시로 Mode A를 대량 기각**한 상태. Mode B·수동 표본이 다음 증거.

---

## 7. 수동 차트 수집 프로토콜 (코딩 전)

목적: 자동화가 아니라 **합의 규칙이 차트에서 보이는지** 표본화.

**자산 후보**: QQQ (또는 NQ) US RTH 우선 · BTC 4h 보조.  
**TF**: 구조 4h/1d, 진입 관찰 15m–1h.  
**표본 목표**: 채널 사건 **≥30건** (Mode A / B / fail 라벨).

각 사건 기록 필드:

```
date | asset | tf_structure | channel_type (asc/desc/flat)
touches_primary | touches_parallel | angle_note (steep/ok/flat)
anchor_notes (vol spike? swing only?)
event: A_bounce | B_break | B_retest_ok | B_retest_fail | fakeout
close_outside? | vol_vs_avg | measured_move_hit?
outcome 1–5 bars / to opposite rail (R multiple, not $)
skip_reason if any
```

규칙: **사후 작도 금지에 가깝게** — 사건 당시 보이는 점만. (불가능하면 “hindsight” 플래그)

산출물:

- [`channel-manual-sample-log.csv`](channel-manual-sample-log.csv) — Batch 1, **n=30**
- [`channel-manual-sample-batch1.md`](channel-manual-sample-batch1.md) — 관찰 요약 + Mode B 규칙 카드 **초안**
- [`data/qqq_usdt_4h.json`](data/qqq_usdt_4h.json) — Bitget QQQUSDT 4H

---

## 8. 수집 완료 게이트 (이전이면 새 전략 코드 금지)

- [x] 빗각 ≡ 추세선/채널 재확인 (공개 2차 소스)
- [x] Mode A/B/C + vol + 3-touch 합의 정리
- [x] 고전 1권 발췌 노트 — [`edwards-murphy-excerpts.md`](edwards-murphy-excerpts.md) (Edwards–Magee Ch.14–15 구조 + Murphy Law #5/#10 공개문)
- [x] 수동 표본 ≥30 (QQQ 4H Batch 1) — **전부 hindsight; 품질 재검증 남음**
- [x] Clearest 3 ICT 병기 — [`channel-clearest3-ict-overlay.md`](channel-clearest3-ict-overlay.md)
- [ ] Mode B만의 **최소 규칙 카드** 1장 **freeze** — 개정안은 excerpts §6 / batch1; 사용자 확정 대기
- [ ] Pitchfork/Fib Channel을 parallel과 분리할지 결정

게이트 통과 후에야 playbook §7 인코딩 재개.

---

## 9. Next (자료수집만)

1. ~~수동 표본 / 고전 발췌 / ICT 병기~~ → **Mode B 카드 freeze** 한 번만 찍기.
2. parallel vs Fib Channel vs pitchfork 분리 결정.
3. 인범 공개 클립에서 **앵커·세션·손절**만 노트로 (룰 복제 X).
4. playbook의 “다음=QQQ Mode B 구현”은 **카드 freeze 뒤로 연기**.

---

## Appendix — 빠른 인용

> “사실 '빗각'이라는 단어는 '추세선'을 다르게 표현한 것일 뿐… 활용 방법 역시 추세선과 100% 일치”  
> — brunch @urbantrader/56

> “It takes two points to draw a trend line, and the third one confirms the validity.”  
> — StockCharts ChartSchool, Trend Lines

> Breakout: decisive **close** outside + volume; prefer **retest** of broken boundary; target ≈ **channel width**.  
> — FinWiz / GrandAlgo / Investing.com academy (요약 합의)
