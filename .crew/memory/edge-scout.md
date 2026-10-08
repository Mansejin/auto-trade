# edge-scout 기억

## 2026-10-08 — T-001 전략 원장
- 한 일: `docs/research/strategy-ledger.md` 작성 (11개 우물, ~160장, 근거 경로 포함). 문서만 읽음, 백테스트 없음.
- 핵심 사실:
  - Policy C: OOS 수익 ≈ B&H(+387 vs +394%), MDD 절반(−37 vs −67%), 2× 수수료 생존. 5y +426%는 in-sample(맵 선택 구간).
  - TrendShortV1(5m di_cloud 숏) LIVE w5, PF 1.44/1.20, 8bps+ 스트레스 실패.
  - 비-OHLCV 부분 생존: AE12 H1(HTX 펀딩 ≤−0.02% → 다음날 KRW-BTC 강세, n=45, 30bps 생존) / AE13 H_rich(김프 ≥90분위 → 약세, n=21). AE7b(OKX/Bitget 펀딩 분위수)는 기각 → 출처 의존성 의심.
  - Williams 1h sideways LIVE 승격 기록(07-29) vs 정본 맵 4h-v5 불일치 — 서버 `regime-current.json` 확인 필요.
- 결정: 판정 라벨은 KILL/PARTIAL/SURVIVE/LIVE/미검증. "형식 생존·net≈0"은 PARTIAL로 두되 승격 근거 아님 명시.
- 다음(T-002) 알아둘 것:
  - 재제안 금지 우물 9개는 원장 §2 목록 참조. BTC OHLCV 파생 카드는 내지 말 것.
  - 덜 판 우물: 펀딩(출처 정합), 호가 불균형(AE12 H2 데이터 미수집), 김프(소표본), 크로스섹션 알트, OI·청산, 상장/공지, 거래소 지연, 변동성 프리미엄.
  - 같은 계열 카드는 사이클당 최대 2장.

## 2026-10-08 — T-002 카드 5장
- 한 일: docs/research/cards/ 에 funding-negative-consensus, funding-carry-btc-eth, kimchi-rich-fade-pooled, xs-alt-momentum-weekly, upbit-listing-fade.
- 결정: AE12는 Binance+Bybit 합의 + 단독 부호 일치로 출처 의존성 차단. AE13은 BTC/ETH/XRP 합산으로 n 확대. 공통 OOS 분할 ≈2023 전후 고정, 무작위 1,000회 상위 5% 기준.
- 데이터 주의: OKX 펀딩 이력은 ~3개월뿐(제외), Binance OI 이력 ~30일(제외). USDKRW는 frankfurter.app(ECB). 업비트 상폐 마켓은 market/all에 없음 → 생존편향 명시.
- 다음: T-005 결과 보고 KILL 카드는 변형 재제안 금지. 남은 우물: OI·청산(무료 장기 이력 확보가 관건), 거래소 지연, 변동성 프리미엄(Deribit DVOL 공개 API 검토).
