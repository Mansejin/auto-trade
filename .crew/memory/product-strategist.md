# product-strategist 기억

## 2026-10-08 · T-006 상품 브리프
- 한 일: docs/product/upbit-listing-alert-brief.md, btc-bear-filter-brief.md, portfolio-overview.md 작성.
- 결정: 첫 출시 = 업비트 상장 이벤트 알림(정보·분포 형태, 매매 지시 없음)을 무료 공개 텔레그램으로 시작 → 포워드 ≥30건(약 6개월) 후 유료 검토. 중단 기준: 포워드 하락 비율 <50% 또는 알트 지수 대비 초과 ≤0.
- 이유: 반증 통과 유일 비-OHLCV 신호, 레드팀이 정보 상품만 허용, scripts/data + bot/telegram_notify.py 재사용.
- SMA200: 공개 규칙 + 수익 우위 VETO → 유료 신호 불가, 무료 리드 마그넷/봇 키트 프리셋만.
- 금지 문구: PF 4.48(사후 관찰), +2040%, 승률 단독, 레버리지 권유. Policy C는 VETO라 상품 증거로 쓰지 않음.
- 다음에 알 것: 법무 답변(유사투자자문업, 거래소 데이터 재배포) 전 결제 열지 말 것. T-007(Policy C 유지 여부) 사용자 결정 대기.

## 2026-10-08 · T-022 SMA200 유료 구독 검토
- 한 일: docs/product/sma200-subscription-brief.md, docs/legal/sma200-subscription/lawyer-questions.md. 보드 T-026(backend-dev 일일 로그), T-027(user: 소액 투입·법무 송부) 추가.
- 결정: 단독 유료 신호 비추천. 추천 = 무료 일일 공개 기록 6개월 → 상장 알림 유료 티어에 월간 레짐 리포트 묶음, 교육 병행. 봇 키트 보류, 호스팅 SaaS·타인 자금 운용 안 함.
- 이유: 공짜 대체재(TradingView MA 알림), 연 6.5회 전환, 포워드 0, 수익 우위 VETO. 금융위·FIU 회신(casenote 9576428932, 사례집 2.0)이 "API 자동매매 SW 개발·공급"도 특금법 VASP 신고 소지로 봄 → 키트·SaaS 모두 법무 차단 질문.
- 다음에 알 것: w1 라이브지만 Upbit KRW≈0 → 실체결 없음, "실거래 수익" 문구 금지. 봇에 일일 판정 로그 없음(T-026). 중단 기준: 기록 누락 월 2일 초과/사후 수정 1건, 대기자 <50, 포워드 MDD < −60%.
