# LIVE 운영 보안 체크리스트

실주문(`PAPER=false`) 전에 아래를 확인하세요. 채팅/깃에 키를 올리지 마세요.

## 1. API 키

- [ ] **출금 권한이 없는** 거래 전용 Open API 키만 사용
- [ ] 허용 IP에 VPS 공인 IP만 등록 (예: `129.225.205.185`)
- [ ] 채팅·스크린샷·커밋에 키가 노출됐다면 **즉시 폐기 후 재발급**
- [ ] 텔레그램 봇 토큰도 노출 시 BotFather에서 revoke 후 재발급
- [ ] Cloudflare API 토큰도 채팅 노출 시 rotate

## 2. `.env` (서버에만 존재)

```env
PAPER=false
LIVE_CONFIRM=I_UNDERSTAND_LIVE_TRADING_RISK
ORDER_FRACTION=0.5          # 권장: 전액(1.0) 지양
MAX_ORDER_KRW=10000         # 1회 상한
MAX_DAILY_LOSS_KRW=3000     # 일일 손실 시 신규 매수 중단 (0=끔)
MAX_CONSECUTIVE_ERRORS=5    # 연속 오류 시 주문 전면 중단
DASHBOARD_TOKEN=긴-랜덤-문자열   # 최소 8자, 권장 16자+
```

- [ ] `chmod 600 .env`
- [ ] `.env`는 gitignore — 절대 커밋하지 않음
- [ ] DESK 비밀번호는 URL(`?token=`)로 넣지 말 것 (로그·히스토리 유출)

## 3. 컨테이너 보안 (compose)

이미 적용: `mem_limit`, `cpus`, `read_only`, `cap_drop: ALL`, `no-new-privileges`, healthcheck.

edge는 **호스트 80만 공개**, 8080은 `127.0.0.1` 바인딩(로컬 디버그용).

## 4. DESK / 프록시 (적용됨)

- 로그인 실패 IP당 5분 8회 제한
- `?token=` 쿼리 인증 제거 (쿠키/Bearer만)
- 보안 헤더: nosniff / DENY frame / no-referrer
- Worker는 `/autotrade*` + GET/HEAD/POST만 전달, hop-by-hop 헤더 최소화

## 5. mem-guard sudo 최소화

호스트에서 `drop_caches`만 허용:

```bash
sudo cp scripts/mem-guard.sudoers /etc/sudoers.d/mem-guard
sudo chmod 440 /etc/sudoers.d/mem-guard
sudo visudo -cf /etc/sudoers.d/mem-guard
```

## 6. 중단 해제

연속 오류/일일 손실로 중단되면 `data/risk.json`의 `trading_halted`를 `false`로 돌리거나 파일을 삭제한 뒤 컨테이너를 재시작합니다. 원인 확인 후에만 해제하세요.

## 7. 키 재발급 후 서버 반영

1. Upbit / Telegram / Cloudflare에서 새 키 발급  
2. 서버 `~/auto-trade/.env`만 수정  
3. `cd ~/auto-trade && docker compose up -d`  
4. `docker compose logs --tail=30 bot` 으로 LIVE 기동·잔고 조회 확인
