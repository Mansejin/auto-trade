# 카드: upbit-listing-fade (업비트 원화 신규상장 펌프 후 해외 무기한 숏)

우물: 상장·공지 이벤트 (1/2) · 상태: frozen 2026-10-08

## 한 줄 원칙
업비트 원화 상장 펌프는 다음 날부터 빠지니, 해외 무기한으로 1주일 숏한다.

## 왜 돈이 나오나
- 업비트 KRW 상장 = 국내 개인 유입 이벤트. 상장 당일 급등(이른바 "업비트 펌프") 후 초기 보유자·해외 차익 물량이 출회된다.
- 손해 보는 쪽: 상장 뉴스 보고 추격 매수한 개인.
- 왜 안 사라지나: 업비트 현물은 숏 불가, 해외 무기한은 펌프 중 펀딩·스퀴즈 위험이 커 다수가 첫날엔 못 들어간다. 진입을 하루 늦춰 스퀴즈 구간을 피한다.

## 데이터
| 시계열 | 무료 엔드포인트 (인증 없음) | 기간 |
|---|---|---|
| 업비트 원화 마켓 목록 | `GET https://api.upbit.com/v1/market/all?isDetails=false` | 현재 상장분 |
| 상장일 = 해당 마켓 최초 일봉 | `GET https://api.upbit.com/v1/candles/days?market=KRW-XXX&to=..&count=200` (과거로 페이징) | 2017-10 ~ |
| 업비트 공지(상장 공지, 보조 확인) | `GET https://api-manager.upbit.com/api/v1/announcements?os=web&page=1&per_page=20&category=trade` (비공식, 누락 가능) | 가능한 범위 |
| Binance USDT-M 무기한 일봉·펀딩 | `GET https://fapi.binance.com/fapi/v1/klines?symbol=XXXUSDT&interval=1d` · `/fapi/v1/fundingRate?symbol=XXXUSDT` | 2019-09 ~ |

생존편향 주의: 상폐된 KRW 마켓은 market/all에 없음 → 공지 API와 data.binance.vision 목록으로 보충, 누락분은 결과에 명시.
대상: 2020-01 이후 KRW 신규상장 중 상장 시점에 Binance USDT-M 무기한이 이미 있던 코인(예상 80~150건).

## 규칙 (하이퍼 2, 값 고정)
- 진입: 업비트 KRW 상장일 D(KST) 기준 **D+1** UTC 00:00 Binance 무기한 시가 숏, 1배.
- 청산: 진입 후 **7일** 시가 매수. 손절 없음.
- 펀딩 지급/수취를 손익에 포함.
- 하이퍼: 진입 지연 1일, 보유 7일.

## 기각 기준 (사전)
- 분할: train 2020-01~2023-06 / OOS 2023-07~2026-09 (상장 날짜 기준).
- 수수료 2배(편도 0.05%×2) + 슬리피지 20bps(알트) + 펀딩 반영 후 OOS PF < 1.1 → KILL.
- OOS 이벤트 < 30 → INCONCLUSIVE.
- 비교: 같은 코인 무작위 7일 숏 1,000회 대비 상위 5% 밖 → KILL. 같은 기간 BTC 7일 숏 대비 초과수익 ≤ 0 → KILL(시장 하락 베타일 뿐).
- 꼬리 위험: 단일 이벤트 손실 > 40%가 OOS에 2회 이상이면 상품 부적합 표기.

## 판매 각도
"업비트 상장 이벤트 리포트" — 상장 후 1주 수급 경보(직접 숏 상품보다 정보 상품으로).
