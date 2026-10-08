# devops memory

## 2026-10-08 T-013 상장 알림 w6
- NAS `p3f8c1a2-w6` = `python -m alerts.listing_alert`, DRY_RUN. 이미지는 `p3f8c1a2-w1:latest` 재사용(build 없음) — w1 이미지를 지우거나 이름 바꾸면 w6도 영향.
- env_file 안 씀(LIVE 키 주입 방지). env: LISTING_ALERT_DRY_RUN/POLL_MINUTES/CHAT_ID, TELEGRAM_BOT_TOKEN만 .env에서 보간.
- 마운트: alerts, bot, scripts, config, docs/sales/upbit-listing-alert (ro), data, logs (rw). `scripts/data/_common.py`가 import 시 `/app/data/research` mkdir 하므로 data rw 필요.
- NAS에 동기화한 파일: alerts/*.py, scripts/data/{_common,fetch_upbit_announcements}.py, config/listing-alert-stats.json, templates.json. 코드 갱신 = sync-files.ps1 -HostAlias nas → `restart w6`.
- 실제 발송 전환은 보드 T-018(to: user).
- sync-files.ps1 기본 HostAlias가 레거시 `saenggibu-nas-local` → 항상 `-HostAlias nas` 넘길 것. 배포 전 로컬/NAS compose md5 비교(이번엔 일치).
- 원격 스크립트는 `Get-Content -Raw x.sh | ssh nas "tr -d '\r' > /tmp/x.sh && sh /tmp/x.sh"`.
