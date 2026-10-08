# 크루 보드

auto: off
<!-- auto: on 이면 팀장 턴이 끝날 때 open 상태이고 to가 user가 아닌 작업이 남아 있으면 훅이 이어서 처리하라고 알린다. 멈추려면 off. -->

목표: 반증을 통과한 엣지를 찾아 판매 상품 브리프까지 만든다. 이후 판매·법무·앱개발팀으로 넘긴다.
파이프라인: 과거 전략 목록 → 발굴(Scout) + 데이터 → 리서치 → 반증 → 상품 기획

## 작업

- [x] T-001 | to: edge-scout | from: user | done | 과거 전략 전수 목록(전략 묘지 + 생존자) 작성
  - 참고: docs/research/, freqtrade-research/reports/, reports/, strategies/, freqtrade-research/user_data/strategies/, docs/*.md(playbook류), VERSION.md
  - 산출물: docs/research/strategy-ledger.md — 전략별 1줄: 이름 | 데이터 우물(OHLCV 패턴/레짐/펀딩 등) | 종목·TF | 판정(KILL/SURVIVE/LIVE/미검증) | 핵심 수치 | 근거 파일
  - 끝에 요약: 우물별 시도 수·생존 수, "이미 판 우물" 목록, 생존·부분 생존 자산(예: Policy C는 OOS에서 B&H 수익과 비슷, MDD 절반)
  - 완료 기준: 기각/생존 판정이 근거 파일과 함께 표로 정리됨
  - 결과: 11개 우물·약 160장 정리. 생존은 Policy C(MDD 엣지만 OOS 재현)와 그 슬리브, TrendShortV1(PARTIAL·LIVE). 비-OHLCV 부분 생존 2건(AE12 H1 펀딩, AE13 김프 rich). 이미 판 우물 9개 목록화 → docs/research/strategy-ledger.md

- [x] T-002 | to: edge-scout | from: lead | done | 새 우물 가설 카드 5장 (T-001 이후)
  - 참고: docs/research/strategy-ledger.md, docs/motto.md, .cursor/agents/edge-scout.md
  - 완료 기준: docs/research/cards/ 에 카드 5장, 비-OHLCV 우물 3장 이상, 무료 공개 데이터로 검증 가능
  - 결과: 카드 5장(펀딩 2, 김프 1, 크로스섹션 알트 1, 상장 이벤트 1; 전부 일봉/주간/이벤트 저회전, 엔드포인트·사전 기각 기준 명시) → docs/research/cards/{funding-negative-consensus,funding-carry-btc-eth,kimchi-rich-fade-pooled,xs-alt-momentum-weekly,upbit-listing-fade}.md

- [x] T-003 | to: red-team | from: lead | done | 기존 생존 자산(Policy C 등) 반증 (T-001 이후)
  - 참고: docs/research/strategy-ledger.md, docs/research/policyC-*.md, docs/research/fair-race-policyC-vs-rebalance.md, scripts/bt_policyC_*.py
  - 완료 기준: docs/research/redteam/policyC.md 에 판정(VETO/PASS-WITH-CAVEATS/PASS)
  - 결과: VETO. 헤드라인 재현됨. 라이브 방식 재실행 시 OOS +387%→+283%(B&H +394%, SMA200 필터 +639% 미만), 상위 5세그먼트 제거 시 OOS −43.5%, 라이브 사이드웨이(williams-v1)는 미검증 → docs/research/redteam/policyC.md, scripts/redteam/policyC_*.py

- [x] T-004 | to: quant-data | from: lead | done | 카드용 데이터 수집 (T-002 이후)
  - 완료 기준: docs/research/data-catalog.md + scripts/data/fetch_*.py
  - 결과: 11개 CSV 수집 완료(펀딩 BTC/ETH Binance+Bybit, 알트 펀딩 207개, 현물·무기한 일봉, 업비트 KRW 292개 마켓, USDKRW, 상폐 포함 Binance USDT 709개 심볼). 카드 4장 테스트 가능, upbit-listing-fade는 부분(상폐된 KRW 마켓 누락) → docs/research/data-catalog.md, scripts/data/

- [x] T-005 | to: quant-researcher | from: lead | done | 카드 5장 백테스트 (T-004 이후)
  - 완료 기준: docs/research/results/<slug>.md 각각 SURVIVE/KILL/INCONCLUSIVE
  - 결과: SURVIVE 1(upbit-listing-fade OOS 133건 PF x2 1.92, 무작위 99.9pct, 단 −40% 초과 손실 6회로 상품 부적합 표기 → T-009), KILL 3(funding-carry: always-on보다 열세·연 2.5%; kimchi: PF 1.005·무작위 70.6pct; xs-momentum: OOS PF 0.82·무작위 8.8pct), INCONCLUSIVE 1(funding-negative-consensus 20건, OOS 4건) → docs/research/results/*.md, scripts/bt_<slug>.py, reports/research-cards/*.json

- [x] T-009 | to: red-team | from: quant-researcher | done | upbit-listing-fade SURVIVE 반증
  - 참고: docs/research/results/upbit-listing-fade.md, scripts/bt_upbit_listing_fade.py, reports/research-cards/upbit-listing-fade.json, docs/research/cards/upbit-listing-fade.md, docs/research/data-catalog.md
  - 점검: 상장 시각(공지 KST)과 D+1 00:00 UTC 진입 대조(09:00 KST 이전 상장 시 첫 일봉 날짜 밀림), 공지 파싱 누락·상폐 마켓 생존편향, 펀딩 부호·스케일(1000XXX 심볼), 2025~26 집중(105/133건)·연도별 안정성, 상위 이벤트 의존, 실제 숏 가능성(신규 무기한 유동성·펀딩 급등), 꼬리 손실(−40% 초과 6회)
  - 완료 기준: docs/research/redteam/upbit-listing-fade.md 판정(VETO/PASS-WITH-CAVEATS/PASS)
  - 결과: 신호 PASS-WITH-CAVEATS / 자동 숏 상품 VETO. 재현 일치. 공지+24h PF 1.93, D+2 1.72, 알트지수 숏 대비 초과 +4.15%/건(무작위 100pct), 무기한 나이>180일 PF 2.27, 상위5 제거 PF 1.65, 펀딩 부호 정확(평균 −3.6%/건). 1배 현실 사이징 MDD −72%·월 −63%, 2·3배 파산. 상폐 무기한 5건+모호 날짜 2건 결함(제거 시 PF 2.02). 2025~26 집중 79% → docs/research/redteam/upbit-listing-fade.md, scripts/redteam/listing_fade_redteam.py

- [ ] T-007 | to: user | from: red-team | blocked | 라이브 CORE(Policy C) 유지 여부 결정
  - 참고: docs/research/redteam/policyC.md — VETO. 라이브식 재현 OOS +283% < B&H +394% < SMA200 필터 +639%. 라이브 횡보 슬리브 williams-v1은 백테스트 없음.
  - 결정할 것: CORE 유지 / SMA200 필터로 교체 / 일시 정지
  - T-008 결과 반영: SMA200은 PASS-WITH-CAVEATS(BTC/ETH 낙폭 축소 오버레이로만). 수익 우위 주장은 불가 — 9년 중 6년 B&H 열세, USD 거래소 기준 1.16배. Policy C보다는 단순·라이브식 성과 우위.

- [x] T-008 | to: red-team | from: lead | done | SMA200 필터(일봉 종가>SMA200이면 BTC 보유, 아니면 현금) 반증
  - 참고: docs/research/redteam/policyC.md, scripts/redteam/policyC_redteam.py
  - 점검: 다음날 체결·수수료 2배, 무작위 진입 1000회 대비 백분위, ETH/XRP 전이, 휩쏘 횟수, 2018 이전·2022 하락장 구간별, 다중검정(사후 선택 여부)
  - 완료 기준: docs/research/redteam/sma200-filter.md 판정
  - 결과: PASS-WITH-CAVEATS(BTC·ETH 위험관리 오버레이 한정). 수수료 x4·체결지연·SMA100~300 고원·2018 이전 BTC 통과, 무작위 95백분위. 수익 헤드라인 VETO: USD 거래소 B&H 대비 1.16x(Upbit 1.50x), 9년 중 6년 B&H 열위, 노출 맞춘 B&H보다 MDD 깊음, XRP 전패 → docs/research/redteam/sma200-filter.md, scripts/redteam/sma200_*.py

- [x] T-006 | to: product-strategist | from: lead | done | 상품 브리프 (T-003, T-005 반증 이후)
  - 완료 기준: docs/product/*-brief.md, 판매·법무·앱개발팀 브리프 포함
  - 결과: 신호 판매 상품 없음. 1순위 = 업비트 상장 이벤트 알림(무료 공개 텔레그램 채널로 포워드 기록 ≥30건·약 6개월 후 유료화 검토), SMA200은 무료 리드 마그넷·봇 키트 프리셋, 교육·봇 키트·리서치 프로세스는 엣지 불필요 대안. Policy C·상장 숏 자동매매 판매 금지 → docs/product/{upbit-listing-alert-brief,btc-bear-filter-brief,portfolio-overview}.md
