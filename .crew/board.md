# 크루 보드

auto: off
<!-- auto: on 이면 팀장 턴이 끝날 때 open 상태이고 to가 user가 아닌 작업이 남아 있으면 훅이 이어서 처리하라고 알린다. 멈추려면 off. -->

목표: 반증을 통과한 엣지를 찾아 판매 상품 브리프까지 만든다. 이후 판매·법무·앱개발팀으로 넘긴다.
파이프라인: 과거 전략 목록 → 발굴(Scout) + 데이터 → 리서치 → 반증 → 상품 기획
2단계(2026-10-08~): 첫 상품 "업비트 상장 이벤트 알림" 실체화 — 판매(sales-marketer)·법무(legal-compliance)·앱개발(backend-dev, devops, qa-tester)

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

- [x] T-007 | to: user | from: red-team | done | 라이브 CORE(Policy C) 유지 여부 결정
  - 참고: docs/research/redteam/policyC.md — VETO. 라이브식 재현 OOS +283% < B&H +394% < SMA200 필터 +639%. 라이브 횡보 슬리브 williams-v1은 백테스트 없음.
  - 결정할 것: CORE 유지 / SMA200 필터로 교체 / 일시 정지
  - 결과: 사용자 결정 2026-10-08 — SMA200 필터로 교체. w1 STRATEGY_PATH=core-btc-sma200-filter-1d.json, 레짐 스위치 크론 비활성(scripts/nas_regime_cron.sh exit 0). Upbit 캔들 200개 초과 페이지네이션 추가(history_bars).
  - T-008 결과 반영: SMA200은 PASS-WITH-CAVEATS(BTC/ETH 낙폭 축소 오버레이로만). 수익 우위 주장은 불가 — 9년 중 6년 B&H 열세, USD 거래소 기준 1.16배. Policy C보다는 단순·라이브식 성과 우위.

- [x] T-008 | to: red-team | from: lead | done | SMA200 필터(일봉 종가>SMA200이면 BTC 보유, 아니면 현금) 반증
  - 참고: docs/research/redteam/policyC.md, scripts/redteam/policyC_redteam.py
  - 점검: 다음날 체결·수수료 2배, 무작위 진입 1000회 대비 백분위, ETH/XRP 전이, 휩쏘 횟수, 2018 이전·2022 하락장 구간별, 다중검정(사후 선택 여부)
  - 완료 기준: docs/research/redteam/sma200-filter.md 판정
  - 결과: PASS-WITH-CAVEATS(BTC·ETH 위험관리 오버레이 한정). 수수료 x4·체결지연·SMA100~300 고원·2018 이전 BTC 통과, 무작위 95백분위. 수익 헤드라인 VETO: USD 거래소 B&H 대비 1.16x(Upbit 1.50x), 9년 중 6년 B&H 열위, 노출 맞춘 B&H보다 MDD 깊음, XRP 전패 → docs/research/redteam/sma200-filter.md, scripts/redteam/sma200_*.py

- [x] T-006 | to: product-strategist | from: lead | done | 상품 브리프 (T-003, T-005 반증 이후)
  - 완료 기준: docs/product/*-brief.md, 판매·법무·앱개발팀 브리프 포함
  - 결과: 신호 판매 상품 없음. 1순위 = 업비트 상장 이벤트 알림(무료 공개 텔레그램 채널로 포워드 기록 ≥30건·약 6개월 후 유료화 검토), SMA200은 무료 리드 마그넷·봇 키트 프리셋, 교육·봇 키트·리서치 프로세스는 엣지 불필요 대안. Policy C·상장 숏 자동매매 판매 금지 → docs/product/{upbit-listing-alert-brief,btc-bear-filter-brief,portfolio-overview}.md

- [x] T-010 | to: legal-compliance | from: lead | done | 상장 알림 규제 쟁점 메모 + 변호사 질의서 + 고지·약관 초안
  - 참고: docs/product/upbit-listing-alert-brief.md (6. 법무팀), docs/product/portfolio-overview.md (법무팀)
  - 완료 기준: docs/legal/upbit-listing-alert/{issues,lawyer-questions,disclaimer-draft,terms-draft}.md, 출처 URL·확인일 포함
  - 결과: 위험 1위 거래소 약관(업비트는 "타인 투자판단 돕는 서비스" 사용 금지, Binance·Bybit·Bitget 상업 재배포 금지 — 유료 높음/무료 중간), 2위 유료 티어의 자문업 해당성(해외 무기한 선물=파생상품 여부 미확인, 가상자산 유사자문업 법안 계류 — 중간), 3위 가상자산이용자보호법 제10조(운영자 선행매매·오인 표시 — 낮음~중간). 레퍼럴 금지(FIU 2025-12-02 경고). 권고: 유료 결제 보류, 방송형 채널·지시어 금지·업비트 시세 미사용·운영자 거래 금지 기간·고정 지연 → docs/legal/upbit-listing-alert/{issues,lawyer-questions,disclaimer-draft,terms-draft}.md

- [ ] T-015 | to: user | from: legal-compliance | blocked | 변호사 질의서 송부 여부·예산 결정 (유료화 전 필수)
  - 참고: docs/legal/upbit-listing-alert/lawyer-questions.md (질문 1이 차단 질문)
  - 결정할 것: 송부 여부, 무료 채널을 변호사 답변 전 개시할지(issues.md 권고 설계 적용 조건), 알림 고정 지연 값
  - 결과:

- [x] T-011 | to: sales-marketer | from: lead | done | 무료 텔레그램 채널 출시안 + 알림 메시지 문구 + 커뮤니티 글 초안
  - 참고: docs/product/upbit-listing-alert-brief.md, docs/research/redteam/upbit-listing-fade.md
  - 완료 기준: docs/sales/upbit-listing-alert/ 에 채널 운영안, 알림·7일 결과 회신 메시지 템플릿(앱개발이 그대로 쓸 수 있게 변수 표기), 커뮤니티 글 2편, 지표·가격 실험안
  - 결과: 채널명 추천 "상장공지 7일 기록"(후보 3), 고정 공지·운영 규칙·6개월 KPI(M6 구독 1,500·포워드 ≥30건)·퍼널, 템플릿 3종(alert/alert_no_perp/followup, 변수 매핑표, 과거 분위수 −28.2/−9.1/+15.0% 가격 기준), 커뮤니티 글 2편, 결제 없는 수요 실험(대기자·설문·A/B). 분포·포워드 집계를 비용 제외 가격 변화로 통일 — 중단 기준 정의 팀장 확인 필요 → docs/sales/upbit-listing-alert/{channel-plan,message-templates,community-posts,pricing-experiments}.md, templates.json

- [x] T-016 | to: user | from: sales-marketer | done | 채널 개설·게시 결정 — 2026-10-08 @listing7d_kr 개설, 소개글·고정 공지(docs/sales/upbit-listing-alert/pinned.txt) 게시. 커뮤니티 글 게시는 미정.
  - 결정할 것: 채널 이름(추천 "상장공지 7일 기록"), 핸들 확보, 커뮤니티 글 2편 게시 여부·시점. 법무 T-010 고지 문구 확정 후 게시 권장.
  - 참고: docs/sales/upbit-listing-alert/channel-plan.md, community-posts.md
  - 팀장 결정(2026-10-08): 공개 집계·중단 기준(30건 하락 비율 < 50%)은 **비용·펀딩 미포함 단순 가격 변화** 기준(누구나 검증 가능). 기록에는 비용·펀딩 포함 값도 함께 남긴다. 과거 기준값: 단순 93/133(69.9%, D+1 시가→D+8 시가) 하락, 비용 포함 63.9%.

- [x] T-012 | to: backend-dev | from: lead | done | 상장 알림 MVP 서비스 구현 (주문 기능 없음)
  - 참고: docs/product/upbit-listing-alert-brief.md (앱개발팀), scripts/data/fetch_upbit_announcements.py, scripts/data/build_listing_perp_map.py, scripts/data/fetch_funding.py, reports/research-cards/upbit-listing-fade.json, bot/telegram_notify.py
  - 완료 기준: 공지 폴링 → 무기한 존재·거래대금·펀딩 조회 → 템플릿 발송 → 7일 뒤 결과 회신 → append-only 기록. 기본 DRY_RUN(발송 대신 로그). 채널 ID는 env(LISTING_ALERT_CHAT_ID). 셀프체크 1개.
  - 결과: `python -m alerts.listing_alert [--once|--replay T ISO]`. 공지 1페이지+market/all diff, 첫 실행은 bootstrap(기존 공지 발송 안 함), Binance/Bybit/Bitget 무기한·1000XXX, 고정 분포 config/listing-alert-stats.json(OOS 133건 p10/50/90 −32.9/−11.2/+12.2%, +30% 고가 19건), sales templates.json 변수명 사용, 7일 회신은 Binance 무기한 있는 건만(판매 문구 "집계 제외" 준수), logs/listing-alerts.jsonl append-only. 셀프체크 `python -m alerts._selfcheck_listing` OK, LIT/CASHCAT replay OK → alerts/listing_alert.py, alerts/_selfcheck_listing.py, scripts/build_listing_alert_stats.py

- [x] T-017 | to: sales-marketer | from: backend-dev | done | templates.json alert_no_perp 수정 (팀장 직접 처리)
  - 참고: docs/sales/upbit-listing-alert/templates.json, alerts/listing_alert.py (FALLBACK, build_alert 변수)
  - 내용: alert_no_perp가 "Binance 없음 / Bybit 없음 / Bitget 없음"을 고정 문자열로 씀. "무기한 없음"은 Binance USDT-M 기준이라 Bybit/Bitget엔 있을 수 있음(예: CASHCAT은 Bybit CASHCATUSDT 있음). `{perp_bybit}` `{perp_bitget}` 변수를 쓰고 "과거 표본(Binance 무기한이 이미 있던 상장)"으로 표기. 추가로 쓸 수 있는 변수: hist_up30_n, hist_up_max_pct, hist_period, age_bucket, age_bucket_n, age_bucket_p50_pct, high_7d_pct, fwd_p50_pct, price_source.
  - 완료 기준: replay `python -m alerts.listing_alert --replay CASHCAT 2026-09-28T14:27:04+09:00` 출력이 사실과 일치
  - 결과:

- [x] T-013 | to: devops | from: lead | done | NAS에 상장 알림 서비스 추가 (T-012 이후)
  - 참고: docker-compose.nas.yml, docs/agents/nas-opaque-names.md, deploy/nas/sync-files.ps1
  - 완료 기준: 새 서비스(난독 이름 규칙 준수) DRY_RUN으로 기동, 로그 확인. 실제 채널 발송 전환은 to: user.
  - 결과: 2026-10-08 NAS `p3f8c1a2-w6` 기동(DRY_RUN=true, CHAT_ID 미설정, w1 이미지 재사용·코드 바인드 마운트, env_file 없이 필요한 env만). bootstrap 기록(기존 공지 8건 skip) + 이후 폴링 정상, `logs/listing-alerts.jsonl`·`data/listing-alert-state.json` 생성. 코드 갱신은 sync-files 후 `restart w6`만 → docker-compose.nas.yml(w6), docs/agents/nas-opaque-names.md, deploy/nas/opaque-names.agent.md

- [x] T-021 | to: growth-pr | from: user | done | @listing7d_kr 채널 홍보안 (채널별 규칙·8주 일정·초안·측정)
  - 참고: docs/sales/upbit-listing-alert/{channel-plan,community-posts,message-templates}.md, pinned.txt, docs/legal/upbit-listing-alert/issues.md
  - 완료 기준: docs/marketing/listing7d/{channels,calendar,tracking}.md + drafts/
  - 결과: 우선순위 1 네이버 블로그(링크 허용·상장 때마다 검색 재유입), 2 X(링크 허용·실시간, 첫 코인 글 자동잠금 주의), 3 코인판(타깃 정확하나 텔레그램 모집은 운영진 사전 동의 필수 → 동의 전 링크 없는 통계 글만). 디시·코인니스는 외부 채널 유도 금지로 보류/제외, 쇼츠는 W5 이후(쇼츠 링크 클릭 불가→프로필), Reddit 등 해외는 법무 권고로 제외. 8주 일정은 첫 알림(E1)·첫 7일 결과(R1)·월간 결산·"160개 전략" 이야기에 연동. 채널별 이름 붙은 초대 링크로 측정, 경고 1회 즉시 중단·4주 10명 미만 중단 규칙. 규칙 출처·확인일(2026-10-08)·미확인 표시 → docs/marketing/listing7d/{channels,calendar,tracking}.md, drafts/{community-stats-post,x-thread,shorts-script,blog-seo-outline}.md

- [ ] T-023 | to: user | from: growth-pr | blocked | 홍보 계정·게시 실행 (사람이 직접)
  - 참고: docs/marketing/listing7d/calendar.md, tracking.md, drafts/
  - 할 일(W1): ① 텔레그램 채널에 이름 붙은 초대 링크 8개 생성(tracking.md 1절) ② TGStat에 채널 등록(Korea/Korean, 소유 인증은 보류 권장) ③ X 계정 준비(전화 인증·프로필 링크=x-profile) 후 소개 트윗 ④ 코인판 운영진에 링크 허용 문의 메일(calendar.md 하단 초안) ⑤ 네이버 블로그 기둥 글 게시(blog-seo-outline.md, 검색량은 네이버 키워드 도구로 확인)
  - 할 일(이후): 첫 알림 뒤 코인판(·선택 디시)에 링크 없는 통계 글 1회, 7일 결과 인용 트윗, W3~4 "160개 전략" 스레드, 월간 결산, W5 쇼츠 제작·유튜브 채널 개설, W6 비트맨 카페 가입해 홍보 규정 확인, 매주 월요일 tracking.md 기록
  - 결정할 것: 위 계정을 만들지(X·네이버 블로그·유튜브·코인판), 실명/브랜드 계정 여부, 스레드 할지
  - 결과:

- [ ] T-024 | to: legal-compliance | from: growth-pr | open | 홍보물 법무 확인 (상표·광고 해당성)
  - 참고: docs/marketing/listing7d/drafts/, docs/legal/upbit-listing-alert/issues.md
  - 질문: (1) 블로그·쇼츠·X에서 "업비트" 이름을 제목·키워드로 쓰는 것, 로고 미사용이면 상표 문제 없는지 (2) 무료 채널을 알리는 홍보물이 유사투자자문 "광고"(제101조의3 필수 기재)로 볼 여지가 있는지, 고지 문구가 충분한지 (3) 홍보물에 과거 분포(133건)를 표로 싣는 것이 쟁점 1(데이터 재배포)과 다른지
  - 완료 기준: issues.md에 홍보물 절 추가 또는 drafts/ 수정 요청 목록
  - 결과:

- [x] T-025 | to: sales-marketer | from: growth-pr | done | community-posts.md 분위수를 채널 값과 일치
  - 참고: docs/sales/upbit-listing-alert/community-posts.md(글 1 표 −28.2/−9.1/+15.0%), config/listing-alert-stats.json(채널 알림 −32.9/−11.2/+12.2%, 기간 2023-07-28..2026-08-24), pinned.txt
  - 이유: 커뮤니티 글과 채널 알림의 분위수가 다르면 공개 직후 "숫자가 다르다"는 지적을 받는다. 홍보 초안(docs/marketing/listing7d/drafts/)은 채널 값으로 썼다.
  - 완료 기준: 공개 문서 분위수·기간이 config와 같은 정의로 통일
  - 결과: 팀장 직접 수정. community-posts.md 표 −32.9/−11.2/+12.2%, 기간 2023-07-28~2026-08-24; message-templates.md 출처를 config/listing-alert-stats.json으로 교체

- [x] T-022 | to: product-strategist | from: user | done | SMA200 필터 유료 구독 상품화 검토 (법무 쟁점 포함)
  - 참고: docs/product/btc-bear-filter-brief.md, docs/research/redteam/sma200-filter.md, docs/legal/upbit-listing-alert/issues.md
  - 완료 기준: docs/product/sma200-subscription-brief.md — 팔 수 있는 형태/없는 형태, 경쟁(무료 대체재), 가격 가설, 출시 전 조건, 법무 질문
  - 결과: 단독 유료 신호 비추천(무료 대체재·연 6.5회·포워드 0·수익 우위 VETO). 추천 = 무료 일일 공개 기록 6개월 → 상장 알림 유료 티어에 월간 "BTC 레짐 리포트" 묶음 + 교육 병행. 봇 키트·호스팅 SaaS 보류(금융위·FIU 회신: API 자동매매 SW 개발·공급도 특금법 VASP 신고 소지), 타인 자금 운용 불가. 실체결 없음(KRW≈0) → 신호 로그 필수·소액 투입은 사용자 결정 → docs/product/sma200-subscription-brief.md, docs/legal/sma200-subscription/lawyer-questions.md

- [ ] T-026 | to: backend-dev | from: product-strategist | open | w1 SMA200 일일 판정 append-only 로그 + 공개 표 1개
  - 참고: docs/product/sma200-subscription-brief.md 4절·7절(앱개발팀), strategies/core-btc-sma200-filter-1d.json, bot/main.py
  - 내용: 일봉 확정 후 하루 1줄(date, close, sma200, state, switched, recorded_at, source), 재시작 중복 금지, 진행 중 봉으로 판정하지 않는지 점검. 전환 시에만 텔레그램 1건(채널은 판매팀 결정). 주문 기능·결제·사용자 키 수집 없음.
  - 완료 기준: 로그 파일 생성·셀프체크 1개, 데스크 읽기 전용 표 또는 정적 파일
  - 결과:

- [ ] T-027 | to: user | from: product-strategist | blocked | SMA200 포워드 기록 방식·법무 송부 결정
  - 결정할 것: (1) Upbit에 소액(예: 30만~50만원) 투입해 실체결 기록을 남길지, 신호 전용 기록만 할지 (2) docs/legal/sma200-subscription/lawyer-questions.md를 상장 알림 질의서(T-015)와 함께 송부할지
  - 결과:

- [x] T-018 | to: user | from: devops | done | 상장 알림 실제 발송 전환 — 2026-10-08 19:10 KST LISTING_ALERT_DRY_RUN=false, CHAT_ID=@listing7d_kr(-1003757343147). 무료 채널만, 유료는 법무 답변 전 금지.
  - 선행: T-015(법무 결정), T-016(채널 개설). 텔레그램 채널 만들고 봇(TELEGRAM_BOT_TOKEN의 봇)을 관리자로 추가.
  - 전환 방법: NAS `/volume1/docker/p3f8c1a2/.env`에 `LISTING_ALERT_CHAT_ID=<채널 ID 또는 @핸들>`, `LISTING_ALERT_DRY_RUN=false` 추가 → `sudo -n /usr/local/bin/docker compose -p p3f8c1a2 -f docker-compose.nas.yml up -d --no-deps w6`. 공개 기록 주소가 생기면 `LISTING_ALERT_RECORD_URL`도(compose w6 environment에 한 줄 추가 필요).
  - 주의: DRY_RUN 기록은 dry_run=true로 남아 라이브 집계(alert_id·fwd_n)와 섞이지 않음. 
  - 결정할 것: 전환 시점(법무 답변 전 무료 채널 개시 여부 포함)
  - 결과:

- [x] T-014 | to: qa-tester | from: lead | done | 상장 알림 MVP 검증 (T-012 이후)
  - 완료 기준: 과거 상장 공지 2~3건 재생 테스트, 공지 API 실패·중복 공지·무기한 없음 경로, 리포트 docs/crew/listing-alert/test-report.md
  - 결과: 22개 중 15 통과·7 실패(전부 버그 재현). 리플레이 NMR/CASHCAT/POD·중복·무기한 없음·1000XXX·D+8 경계·재시작·append-only·DRY_RUN 무발송·템플릿 폴백·금지어·통계 재생성 일치 OK. 버그: B1 Binance 장애를 "무기한 없음"으로 발송(Major), B2 DRY_RUN→LIVE 전환 시 dry-run 알림의 7일 회신이 실채널로 나감(Major, T-018 주의 문구와 반대), B3 상태 저장이 run_once 끝뿐→중간 종료 시 중복 알림, B4 bootstrap 중 공지 API 실패 줄 폴링마다 누적, B5 market/all 장애도 "누락" 집계, B6 −0.04%가 반올림으로 하락 제외, B7 공개 기준 "89/133"이 가격 정의로는 93/133 → T-019, T-020 · alerts/_test_listing_alert.py, docs/crew/listing-alert/test-report.md

- [x] T-019 | to: backend-dev | from: qa-tester | done | 상장 알림 버그 B1~B6 수정 (T-018 실발송 전환 전 필수: B1·B2)
  - 참고: docs/crew/listing-alert/test-report.md (버그 표), alerts/_test_listing_alert.py (테스트 이름=재현), alerts/listing_alert.py
  - 내용: B1 `snapshot`의 `binance_error`를 무기한 없음과 구분(문구 "확인 실패", 집계 제외 여부 정의) / B2 `due_followups`가 현재 모드(`dry_run`)의 알림만 회신 / B3 알림마다 상태 저장 또는 기록(notice_id+ticker) 기준 중복 방지 / B4 bootstrap 실패 시 `down` 상태 유지 / B5 `fwd_missed_n` 정의를 알림 누락(alert_error, 회신 데이터 없음)으로 한정(lead 확인) / B6 하락 판정을 반올림 전 값으로
  - 완료 기준: `python -m alerts._test_listing_alert` 실패 중 B7(문서) 외 전부 통과, `python -m alerts._selfcheck_listing` OK
  - 결과: 21/22 통과(남은 1건 = B7 문서), 셀프체크 OK. B1 Binance 조회 실패=“확인 실패”+분포 알림, 회신 때 무기한 재확인(없으면 followup_skipped) / B2 실제 발송된(sent·live) 알림만 공개 회신, 나머지는 dry 기록 / B3 시작 시 jsonl의 alert로 seen 병합 + 회신 전 상태 저장 / B4 bootstrap 실패 시 down 플래그만 저장(bootstrapped 플래그) / B5 누락=alert_error+회신 데이터 없음+공지 API 장애만 / B6 ret_7d_raw로 하락 판정 → alerts/listing_alert.py, alerts/_selfcheck_listing.py

- [x] T-020 | to: lead | from: qa-tester | done | 공개 기준값 "단순 가격 89/133 하락" 정정 확인
  - 참고: docs/crew/listing-alert/test-report.md B7, docs/sales/upbit-listing-alert/community-posts.md(24행), message-templates.md(89행), T-016 팀장 결정
  - 내용: 알림·통계와 같은 정의(Binance 무기한 D+1 시가→D+8 시가, 비용·펀딩 제외)로 다시 세면 93/133(69.9%). 89는 리서치 카드 `gross>0`(다른 정의). 문서·결정 수치를 93/133으로 고칠지 결정, 필요하면 sales-marketer에 전달.
  - 완료 기준: 공개 문서 수치와 config/listing-alert-stats.json 정의 일치
  - 결과: 93/133(69.9%)로 통일 — community-posts.md, message-templates.md, T-016 결정 줄 수정. B5 "누락" 정의는 알림 자체 누락(alert_error·회신 데이터 없음)으로 한정.
