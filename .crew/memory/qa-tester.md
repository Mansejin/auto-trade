# qa-tester 기억

## 2026-10-08 T-014 상장 알림 MVP 검증
- 테스트: `python -m alerts._test_listing_alert` (plain assert, check 데코레이터로 실패도 계속 집계, 임시 BOT_ROOT, 모듈 전역 함수 monkeypatch). 리플레이 2개만 실제 네트워크, `LISTING_TEST_OFFLINE=1`이면 건너뜀.
- 결과 15/22 통과. 버그 B1~B6 → T-019(backend-dev), B7 기준값 89 vs 93 → T-020(lead). 리포트 docs/crew/listing-alert/test-report.md
- 결정: 버그 재현 테스트는 기대값을 약화하지 않고 실패로 둔다. T-019 완료 후 같은 명령으로 재검증(B7 테스트는 문서 정정 후 config가 아니라 docs 수치 확인이라 실패 지속 가능 → 그때 테스트 기준을 93으로 바꿀지 lead 결정 따름).
- 알아둘 것: 통계 재생성 테스트는 config/listing-alert-stats.json을 덮어쓰므로 원본 바이트 복원 처리함. listing_alert는 import 시 DRY_RUN·경로 결정 → env는 import 전에 설정.
