# 카드: funding-negative-consensus (펀딩 음수 합의 → BTC 현물 매수)

우물: 펀딩 (1/2) · 상태: frozen 2026-10-08 · 출처: AE12 H1 재카드(HTX만 생존, OKX/Bitget 기각 → 출처 의존성 해소가 목적)

## 한 줄 원칙
두 거래소 BTC 펀딩이 동시에 음수면, 숏이 돈을 내고 버티는 중이니 현물을 산다.

## 왜 돈이 나오나
- 펀딩 음수 = 무기한 숏 쏠림. 숏이 롱에게 이자를 내며 버티는 상태라 청산·숏커버가 나오면 현물이 끌려 올라간다.
- 손해 보는 쪽: 레버리지 숏(펀딩 + 숏스퀴즈). 
- 왜 안 사라지나: 음수 구간은 드물고(연 수십 회) 공포장에 나와서 대형 자금은 "떨어지는 칼"로 보고 피한다. 수익이 소수 이벤트에 몰려 있어 차익거래 수요가 작다.
- AE12와 차이: 단일 출처(HTX)가 아니라 **두 독립 출처의 합의**를 요구해 출처 의존성을 사전 차단.

## 데이터
| 시계열 | 무료 엔드포인트 (인증 없음) | 기간 |
|---|---|---|
| Binance BTCUSDT 펀딩 8h | `GET https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&startTime=..&limit=1000` | 2019-09 ~ |
| Bybit BTCUSDT 펀딩 8h | `GET https://api.bybit.com/v5/market/funding/history?category=linear&symbol=BTCUSDT&endTime=..&limit=200` | 2020-03 ~ |
| Upbit KRW-BTC 일봉 (체결) | `GET https://api.upbit.com/v1/candles/days?market=KRW-BTC&to=..&count=200` | 2017-09 ~ |

일 단위 펀딩 = UTC 일자의 8h 3회 평균. 6년+ 확보 가능.

## 규칙 (하이퍼 3, 값 고정)
- 신호: UTC D일 Binance 일평균 펀딩 ≤ **−0.005%** **그리고** Bybit 일평균 펀딩 ≤ −0.005% (같은 임계값).
- 진입: D+1 Upbit KRW-BTC 09:00 KST 일봉 시가 매수 (전액 1단위).
- 청산: 보유 **3일** 후 시가 매도. 보유 중 신호 재발생은 무시(비중첩).
- 하이퍼: 임계값 −0.005%, 보유 3일, 합의 거래소 수 2.

## 기각 기준 (사전)
- 분할: train 2020-03~2023-06 / OOS 2023-07~2026-09 고정. OOS에서 이벤트 평균 수익 ≤ 0 → KILL.
- 수수료 왕복 2배(Upbit 0.05%×2×2 = 20bps) + 슬리피지 10bps 후 OOS PF < 1.1 → KILL.
- 비중첩 거래 전체 < 30회 → INCONCLUSIVE(승격 금지).
- 비교: 같은 3일 보유를 무작위 날짜로 1,000회 → OOS 평균이 상위 5% 밖이면 KILL. B&H 대비 노출당 수익(수익/보유일) 열세면 KILL.
- 출처 검증: Binance 단독, Bybit 단독 신호 각각도 OOS 평균 부호가 같아야 함. 하나라도 반대면 KILL.

## 판매 각도
"공포 매수 알림" — 숏 쏠림 확인 시 현물 분할매수 신호(연 10~30회, 저회전).
