# Auto-Trade Version Registry

**App Version: 0.5.0** (2026-07-29)

---

## Module Versions

| Module | Version | Description |
|--------|---------|-------------|
| **bot/core** | 0.5.0 | 듀얼 거래소(Upbit+Bitget) 메인 루프, 시그널 평가, 주문 실행 |
| **bot/risk** | 0.3.0 | 일일 손실 한도, 연속 에러 중단, HMAC 무결성, 외부 유출 리베이스 |
| **bot/transfer** | 0.4.0 | TRX 브릿지 양방향(Upbit↔Bitget), 자동/수동 이체, 쿨다운 |
| **bot/rebalance** | 0.2.0 | 50:50 하이브리드 리밸런스 + 원화 준비, Telegram 승인 플로우 |
| **bot/signals** | 0.2.0 | 조건 그룹(AND/OR), cross_above/below, 15개 지표 |
| **bot/telegram** | 0.3.0 | 알림 + 명령어(/이체, /리밸런스, /원화준비, /자산 등) |
| **web/desk** | 0.3.0 | FastAPI 대시보드, TradingView 차트, Bitget 잔고 표시 |
| **infra/docker** | 0.2.0 | 4 서비스(bot, bot-bitget, desk, edge), 보안 강화 컨테이너 |
| **infra/cloudflare** | 0.1.0 | Worker 리버스 프록시(mansejin.com/autotrade) |
| **strategies** | 0.2.0 | SMA 크로스 3종(Upbit BTC, Bitget BTCUSDT) |

---

## Changelog

### v0.5.0 (2026-07-29)
- fix: Bitget 자산 이중 집계 제거 (usdtEquity에 TRX 포함)
- fix: 자동 펀딩 후 Upbit risk rebase 누락 수정
- feat: Idle TRX→USDT 자동 환전 (HOLD 시)
- feat: 대시보드에 Bitget 잔고 표시

### v0.4.0 (2026-07-29)
- feat: TRX 브릿지 양방향 구현 (Upbit↔Bitget)
- feat: 50:50 하이브리드 리밸런스 + 밴드(±12%) 자동 감지
- feat: /원화준비 명령 + ensure_upbit_krw
- feat: 전략 자동 펀딩 (선물 진입 시 USDT 부족 → TRX 브릿지)
- fix: 일일 손실 계산에서 이체를 PnL 손실로 오인하는 문제

### v0.3.0 (2026-07-29)
- feat: Bitget UTA v3 API 통합 (선물 + 스팟 통합 계좌)
- feat: Telegram 명령어 체계 확대
- fix: Bitget withdrawal endpoint/precision 수정

### v0.2.0 (2026-07-28)
- feat: Docker Compose 보안 강화 (read_only, cap_drop ALL)
- feat: HTTPS origin + Cloudflare Worker 배포
- feat: HMAC 기반 risk.json 무결성 보호

### v0.1.0 (2026-07-27)
- Initial: Upbit SMA 크로스 봇, Paper/Live 모드
- FastAPI 대시보드 + TradingView 차트
- Telegram 알림 기본 구조

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────────┐
│  Cloudflare Worker (mansejin.com/autotrade)                 │
│    ↓ proxy                                                  │
│  nginx edge (:80/:443) → desk (FastAPI :8080)              │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  Docker Compose (Oracle VPS)                                │
│                                                             │
│  ┌─────────────┐  ┌─────────────────┐  ┌───────────────┐  │
│  │ bot (Upbit) │  │ bot-bitget      │  │ desk          │  │
│  │ KRW-BTC 1d  │  │ BTCUSDT-F 1h   │  │ Dashboard     │  │
│  └──────┬──────┘  └────────┬────────┘  └───────────────┘  │
│         │                   │                               │
│         └─── TRX Bridge ────┘                               │
│              (auto-fund / rebalance)                         │
└────────────────────────────────────────────────────────────┘

Upbit (KRW Spot) ←──TRX──→ Bitget (USDT-M Futures / UTA)
```

## Feature Status

| Feature | Status | Notes |
|---------|--------|-------|
| Upbit KRW 자동매매 | ✅ Live | SMA 크로스, Paper/Live |
| Bitget USDT-M 선물 | ✅ Live | UTA 통합 계좌, 격리 마진 |
| TRX 브릿지 (U→B) | ✅ Live | KRW→TRX 매수→출금→USDT 환전 |
| TRX 브릿지 (B→U) | ✅ Live | USDT→TRX 매수→출금→KRW 매도 |
| 자동 펀딩 | ✅ Live | 선물 진입 시그널 자동 트리거 |
| Idle TRX→USDT | ✅ Live | HOLD 시 5+ TRX 자동 환전 |
| 리밸런스 | ✅ Live | 50:50 ±12%, Telegram 승인 |
| 대시보드 | ✅ Live | Upbit + Bitget 잔고, 차트 |
| 일일 손실 관리 | ✅ Live | HMAC 무결성, 이체 리베이스 |
| 전략 백테스트 | ✅ Agent Skill | uvx 기반 CLI |
| 전략 생성 | ✅ Agent Skill | 자연어→JSON |
