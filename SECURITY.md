# LIVE 운영 보안 체크리스트

실주문(`PAPER=false`) 전에 아래를 확인하세요. 채팅/깃에 키를 올리지 마세요.

## 1. API 키

- [ ] **출금 권한이 없는** 거래 전용 Open API 키만 사용
- [ ] 허용 IP에 VPS 공인 IP만 등록 (예: `129.225.205.185`)
- [ ] 채팅·스크린샷·커밋에 키가 노출됐다면 **즉시 폐기 후 재발급**
- [ ] 텔레그램 봇 토큰도 노출 시 BotFather에서 revoke 후 재발급
- [ ] Cloudflare API 토큰도 채팅 노출 시 rotate

## 1b. Bitget + 이체 (텔레그램 / 전략 자동)

- [ ] Bitget 키는 **System-generated (HMAC)** + IP `129.225.205.185`
- [ ] 봇/이체는 **UTA v3** (`/api/v3/...`) — Classic mix v2 아님
- [ ] Cursor MCP(`@bitget-ai/bitget-agent-mcp`)는 기본 `--read-only`; 키는 `.cursor/mcp.json`에만 로컬 기입 (커밋 금지)
- [ ] 자동 자금: **Upbit KRW→TRX → Bitget TRX→USDT** (UTA 통합 증거금; 별도 선물 이체 불필요)
- [ ] 이체 기능을 쓸 때만 양 거래소 API **Withdraw ON**, 사용 후 다시 OFF 검토
- [ ] `TRANSFER_ENABLED=false` 기본 — 켤 때만:
  - `TRANSFER_CONFIRM=I_UNDERSTAND_TRANSFER_RISK`
  - `TRANSFER_MAX_AMOUNT` **필수 (>0)** — 자동이체 상한(코인 수량)
  - `TRANSFER_WHITELIST_BITGET_USDT` = Bitget 트론 입금주소 (TRX alias로도 사용)
  - (선택) `TRANSFER_WHITELIST_UPBIT_USDT` — Bitget→Upbit 수동 이체용
  - `TRANSFER_COOLDOWN_SEC` (기본 1800) — 연속 출금 방지
- [ ] 전략 `funding.enabled=true` 이면 **매수 시그널 + Bitget USDT 부족** 시 승인 없이 TRX 브릿지 실행
  - `top_up_krw` 예산으로 KRW-TRX 매수 → Upbit TRX 출금 → Bitget에서 TRX→USDT 환전 후 선물 진입
- [ ] 텔레그램 `/이체요청` → `/이체승인` 은 수동 경로 (자동 이체와 별개)
- [ ] `REBALANCE_ENABLED` — 5:5±밴드 하이브리드(알림→`/리밸런스승인`). 기본 밴드 12%p, 알림 쿨다운·`TRANSFER_COOLDOWN`로 잦은 이체 제한
- [ ] `/원화준비 <원>` — Bitget→Upbit TRX 브릿지 + Upbit KRW 매도 제안→승인
- [ ] Bitget→Upbit 에 `TRANSFER_WHITELIST_UPBIT_TRX`(또는 USDT 트론 alias) + Bitget Withdraw
- [ ] `bot-bitget` 은 `TELEGRAM_COMMANDS=false` (명령 수신은 Upbit `bot`만)

## 2. `.env` (서버에만 존재)

```env
PAPER=false
LIVE_CONFIRM=I_UNDERSTAND_LIVE_TRADING_RISK
ORDER_FRACTION=0.5          # 권장: 전액(1.0) 지양
MAX_ORDER_KRW=10000         # 1회 상한
MAX_DAILY_LOSS_KRW=3000     # 일일 손실 시 신규 매수 중단 (0=끔)
MAX_CONSECUTIVE_ERRORS=5    # 연속 오류 시 주문 전면 중단
DASHBOARD_TOKEN=긴-랜덤-문자열   # 최소 32자 (openssl rand -hex 32 권장)
```

- [ ] `chmod 600 .env`
- [ ] `.env`는 gitignore — 절대 커밋하지 않음
- [ ] DESK 비밀번호는 URL(`?token=`)로 넣지 말 것 (로그·히스토리 유출)

## 3. 컨테이너 보안 (compose)

이미 적용: `mem_limit`, `cpus`, `read_only`, `cap_drop: ALL`, `no-new-privileges`, healthcheck.

edge는 **호스트 80만 공개**, 8080은 `127.0.0.1` 바인딩(로컬 디버그용).

## 4. DESK / 프록시 (적용됨)

- 로그인 실패 IP당 5분 8회 제한 (`X-Real-IP` 기준 — 클라이언트 XFF 스푸핑 무시)
- nginx `/login` edge rate limit (1r/s, burst 5)
- 로그인/로그아웃 CSRF 토큰 (HMAC, `DASHBOARD_TOKEN` 기반)
- `?token=` 쿼리 인증 제거 (쿠키/Bearer만)
- CSP + 보안 헤더: nosniff / DENY frame / no-referrer
- Worker → origin **HTTPS** (`https://autotrade-origin.mansejin.com`)
- LIVE 시 `risk.json` HMAC 무결성 (`UPBIT_SECRET_KEY` 기반, 변조 시 거래 중단)
- `data/state.json`, `data/risk.json` 저장 시 `chmod 600`

## 5. mem-guard sudo 최소화

호스트에서 `drop_caches`만 허용:

```bash
sudo cp scripts/mem-guard.sudoers /etc/sudoers.d/mem-guard
sudo chmod 440 /etc/sudoers.d/mem-guard
sudo visudo -cf /etc/sudoers.d/mem-guard
```

## 6. 중단 해제

연속 오류/일일 손실로 중단되면 원인 확인 후 `data/risk.json`을 수정합니다.  
LIVE 모드에서는 파일에 `_integrity` HMAC이 포함되므로, 수동 편집 시 서명이 깨지면 **거래가 자동 중단**됩니다.  
안전한 해제: 봇 중지 → `risk.json` 삭제 또는 `trading_halted`/`halt_buys_only`/`halt_reason`만 수정 후 봇 재시작(다음 save 시 재서명).

## 7. 키 재발급 후 서버 반영

1. Upbit / Telegram / Cloudflare에서 새 키 발급  
2. 서버 `~/auto-trade/.env`만 수정  
3. `cd ~/auto-trade && docker compose up -d`  
4. `docker compose logs --tail=30 bot` 으로 LIVE 기동·잔고 조회 확인
