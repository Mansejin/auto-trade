# backend-dev memory

## 2026-10-08 T-012 상장 알림 MVP
- 코드: alerts/listing_alert.py (loop/--once/--replay), alerts/_selfcheck_listing.py, scripts/build_listing_alert_stats.py → config/listing-alert-stats.json (오프라인 1회, 재학습 없음).
- 경로: 상태·기록은 BOT_ROOT(기본 repo 루트) 아래 data/listing-alert-state.json, logs/listing-alerts.jsonl. stats·templates는 코드 위치(CODE) 기준.
- 재사용: scripts/data/fetch_upbit_announcements(URL/LISTING/TICKER), scripts/data/_common.get(재시도), bot/telegram_notify.TelegramNotifier. → Docker 이미지에 scripts/data, config, docs/sales 포함 필요(T-013).
- 결정: 템플릿 변수명은 sales templates.json에 맞춤. no-perp 알림은 7일 회신 없음(판매 문구 "집계 제외"), 그래서 Upbit 캔들 경로 삭제. 첫 실행은 bootstrap 줄만 남기고 기존 공지 발송 안 함. 소스 장애는 down/recovered 전환 시 1줄씩만 기록.
- 금지어(BANNED) 포함 템플릿은 내장 fallback으로 대체, DISCLAIMER 없으면 자동 추가.
- 2026-10-08 T-019: QA 테스트 `python -m alerts._test_listing_alert`(수정 금지, B7 문서 1건만 실패 예상). jsonl이 정본(시작 시 seen 병합), state의 `bootstrapped` 플래그, binance_error=미확인(대상 유지·회신 때 재확인), 공개 회신은 live+sent 알림만, 하락 판정은 ret_7d_raw.
- 한계: replay의 거래대금·펀딩은 현재값(과거 시점 아님). Binance 펀딩은 lastFundingRate(직전 정산, 주기 4h/8h 구분 안 함).
