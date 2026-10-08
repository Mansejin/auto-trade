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
- 알아둘 것: 거래소·시작일 민감도를 항상 같이 본다. "초과수익"보다 "노출 맞춘 B&H 대비 Sharpe"가 정직한 지표다. SMA100/150이 더 좋아 보여도 사후 선택이므로 바꾸지 말 것.
