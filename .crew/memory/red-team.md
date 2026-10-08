# red-team 기억

## 2026-10-08 T-003 Policy C → VETO
- 한 일: Policy C 헤드라인(IS +425.9/−32.2, OOS +387.4/−36.7)을 툴킷으로 정확히 재현. 분류기 룩어헤드(같은 날 종가 + MIN_RUN=14 사후 병합)를 라이브 방식(전날 원시 레이블)으로 바꿔 재실행 → IS +428.5/−27.7, OOS +283.3/−37.2.
- 판정 이유: OOS에서 SMA200 한 줄 필터(+639/−47, 50% 비중 +198/−27)의 경계선 아래. 상위 5세그먼트 제거 시 OOS −43.5%. 라이브 사이드웨이는 williams-v1인데 백테스트는 v5.
- 알아둘 것:
  - 원본 산출물은 reports/에 없고 git 이력에만 있다(82b9381 path, 025fa93 OOS, daeb8ac fair race). `git show <sha>:<path>`로 복원.
  - 툴킷 CLI는 로컬에 설치되어 있다. 세그먼트 하나당 약 4초. `scripts/redteam/_bt_cache/`는 gitignore 대상.
  - `segment_daily_equity_v2`의 아핀 스케일링은 MDD를 부풀릴 수 있다. 연속 MDD는 근사치로만 볼 것.
  - 다음 반증 대상 기준선: SMA200 필터(비중 50~100%)를 단순 대안으로 항상 함께 돌린다.

## 2026-10-08 T-008 SMA200 필터 → PASS-WITH-CAVEATS
- 한 일: `scripts/redteam/sma200_data.py`(Upbit/Binance/Bitstamp 일봉 캐시 `_data/`), `sma200_redteam.py`(시가 체결, 수수료 x1/2/4, 무작위 1000회, 전이, 연도별, 인접값, 노출 매칭). 약 1분.
- 판정 이유: BTC·ETH에서 비용·지연·인접값·2018 이전 모두 생존(Upbit 전체 무작위 95백분위). 하지만 수익 우위는 Upbit 원화 경로 효과가 크다(같은 창 Upbit 1.50x vs USD 1.16x B&H). Bitstamp 2018-01 시작이면 B&H 미만. 9년 중 6년 B&H 열위. MDD 개선은 대부분 평균 노출 53% 효과(고정 53%가 MDD 더 얕음). XRP는 SMA100~300 전부 실패.
- 알아둘 것(T-008): 거래소·시작일 민감도를 항상 같이 본다. "초과수익"보다 "노출 맞춘 B&H 대비 Sharpe"가 정직한 지표다. SMA100/150이 더 좋아 보여도 사후 선택이므로 바꾸지 말 것.

## 2026-10-08 T-009 upbit-listing-fade → 신호 PASS-WITH-CAVEATS / 자동 숏 VETO
- 한 일: `scripts/redteam/listing_fade_redteam.py`(약 30~50초): 재현, 공지+24h·D+2·D+3 진입, 무기한 나이 버킷, 알트지수(현물 상위30) 숏 초과·무작위 상위100 알트, 펀딩 원자료 대조, 티커 충돌(업비트 원화/환율 vs 무기한 가격비), 사이징 1/2/3배 청산 시뮬, 손절 +30% sanity.
- 판정 이유: 신호는 타이밍·베타·신규상장 효과·상위5 제거 모두 생존. 그러나 1배 현실 사이징 MDD −72%·월 −63%, 2·3배 파산 → 상품은 정보/알림만.
- 알아둘 것: `binance_perp_listing_1d`에 상폐 후 거래량 0 평탄 봉이 있다(AI, B3, GAL, RAY, XCN) → 체결 가능성 점검 시 quote_volume==0 거르기. 이벤트 숏은 평균 PF보다 사이징 경로(동시 보유 적을 때 한 방)가 판정을 가른다. 펀딩은 1h 정산 코인에서 주 −50%까지 나온다.
