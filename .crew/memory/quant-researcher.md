# quant-researcher 기억

## 2026-10-08 T-005 카드 5장 백테스트
- 결과: upbit-listing-fade SURVIVE(→ T-009 red-team), funding-carry / kimchi-rich-fade / xs-alt-momentum KILL, funding-negative-consensus INCONCLUSIVE(20건).
- 코드: `scripts/bt_cards_common.py`(stdlib 전용 로더·PF·요약·백분위, pandas 없음) + `scripts/bt_<slug>.py`. JSON은 `reports/research-cards/<slug>.json`.
- 결정
  - 표본 게이트(<30)는 거래 통계 검정(PF, 무작위)보다 우선해 INCONCLUSIVE로 둔다. 일별 곡선으로 재는 구간 기준(연 4% 허들, always-on 비교)은 게이트와 무관하게 KILL 근거가 된다(carry 판정에 적용).
  - 캐리: 명목을 매일 자기자본/2로 재설정. 고정 수량 1배 숏은 2020~21년 ETH 20배 상승 때 청산되고 펀딩이 부풀려진다.
  - 이벤트가 겹치는 카드(listing)는 전액 순차 복리가 무의미 → 고정 금액 합·중앙값·상위 5건 제외 평균으로 본다.
  - 김프: USDKRW ECB는 D일 고시(13:15 UTC)가 D 종가 전이라 그날 값 사용, 이후 forward-fill만.
- 다음에 알 것
  - 비용 해석: 카드의 "슬리피지 Xbps"는 왕복으로 읽었다(카드 1 문구 기준). 편도로 읽으면 listing x2 비용이 0.6%가 되는데 PF 여유(1.92)가 커서 판정은 같다.
  - 업비트 상장 이벤트는 2022-01 이후 공지가 있어 OOS 생존편향은 묶인다. train(2020~21)은 묶이지 않는다.
  - 2023년 이후 Binance·Bybit 동시 음수 펀딩은 거의 없다(OOS 4건).
