# 크루 보드

auto: on
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

- [ ] T-002 | to: edge-scout | from: lead | open | 새 우물 가설 카드 5장 (T-001 이후)
  - 참고: docs/research/strategy-ledger.md, docs/motto.md, .cursor/agents/edge-scout.md
  - 완료 기준: docs/research/cards/ 에 카드 5장, 비-OHLCV 우물 3장 이상, 무료 공개 데이터로 검증 가능
  - 결과:

- [ ] T-003 | to: red-team | from: lead | open | 기존 생존 자산(Policy C 등) 반증 (T-001 이후)
  - 참고: docs/research/strategy-ledger.md, docs/research/policyC-*.md, docs/research/fair-race-policyC-vs-rebalance.md, scripts/bt_policyC_*.py
  - 완료 기준: docs/research/redteam/policyC.md 에 판정(VETO/PASS-WITH-CAVEATS/PASS)
  - 결과:

- [ ] T-004 | to: quant-data | from: lead | open | 카드용 데이터 수집 (T-002 이후)
  - 완료 기준: docs/research/data-catalog.md + scripts/data/fetch_*.py
  - 결과:

- [ ] T-005 | to: quant-researcher | from: lead | open | 카드 5장 백테스트 (T-004 이후)
  - 완료 기준: docs/research/results/<slug>.md 각각 SURVIVE/KILL/INCONCLUSIVE
  - 결과:

- [ ] T-006 | to: product-strategist | from: lead | open | 상품 브리프 (T-003, T-005 반증 이후)
  - 완료 기준: docs/product/*-brief.md, 판매·법무·앱개발팀 브리프 포함
  - 결과:
