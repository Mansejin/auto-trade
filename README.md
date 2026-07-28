# auto-trade

업비트 공식 [upbit-strategy-toolkit](https://github.com/upbit-official/upbit-strategy-toolkit)로  
전략 JSON·백테스트를 하고, 같은 전략으로 **PAPER 자동매매 봇**을 Docker Compose로 돌리는 저장소입니다.

기본값은 `PAPER=true`입니다. 실주문은 명시적으로 끌 때까지 실행되지 않습니다.

## Layout

```text
.
|-- bot/                     # PAPER/LIVE 봇
|-- web/                     # DESK 대시보드 (TradingView)
|-- strategies/              # 전략 JSON
|-- reports/                 # 백테스트 CSV
|-- data/                    # 런타임 상태 (gitignore)
|-- docker-compose.yml
|-- Dockerfile
`-- .env.example
```

## 전략

| slug | market | timeframe |
|------|--------|-----------|
| `sma_cross_btc` | KRW-BTC | 1d |

- 매수: SMA5 `cross_above` SMA20
- 매도: SMA5 `cross_below` SMA20
- 손절/익절: -5% / +15%

## PAPER 봇이 지원하는 전략 스키마

upbit-strategy-toolkit ConditionGroup JSON과 호환됩니다.

**지표 (15종)**  
`moving_average`(SMA/EMA), `rsi`, `macd`, `bollinger_bands`, `atr`, `stochastic_slow`, `williams_r`, `adx`, `obv`, `cci`, `stochastic_rsi`, `mfi`, `disparity`, `envelopes`, `ichimoku_cloud`

**조건**  
- operand: `indicator` / `field` / `literal` (+ `offset`)  
- op: `gt` `lt` `gte` `lte` `eq` `cross_above` `cross_below`  
- group: nested `AND` / `OR`  
- `stop_loss` / `take_profit`

신호는 **완성 봉**만 사용합니다(진행 중 봉 제외).

## PAPER 봇 (Docker Compose)

### 로컬 / Oracle VPS Ubuntu

```bash
cp .env.example .env
# PAPER=true 유지

docker compose up -d --build
docker compose logs -f bot
```

상태 파일: `data/state.json`  
전략 마운트: `strategies/` (읽기 전용)

중지:

```bash
docker compose down
```

### 환경 변수

| 변수 | 기본 | 설명 |
|------|------|------|
| `PAPER` | `true` | `true`면 가상 체결만 |
| `STRATEGY_PATH` | `/app/strategies/sma_cross_btc.json` | 전략 파일 |
| `POLL_SECONDS` | `300` | 폴링 주기(초) |
| `PAPER_CASH` | `1000000` | 페이퍼 시작 현금(KRW) |
| `FEE_RATE` | `0.0005` | 수수료율 |
| `ORDER_FRACTION` | `1.0` | 매수 시 가용 KRW 비중 (0~1] |
| `MAX_ORDER_KRW` | `0` | 1회 매수 상한(원). `0`=무제한 |
| `MAX_DAILY_LOSS_KRW` | `0` | 일일 손실 한도. 초과 시 신규 매수 중단 |
| `MAX_CONSECUTIVE_ERRORS` | `5` | 연속 틱 오류 시 주문 전면 중단 |

### 실주문 (비권장·명시 옵트인)

`PAPER=false` + API 키 + 아래 확인 문자열이 **모두** 있어야만 실주문이 가능합니다.

```env
PAPER=false
UPBIT_ACCESS_KEY=...
UPBIT_SECRET_KEY=...
LIVE_CONFIRM=I_UNDERSTAND_LIVE_TRADING_RISK
```

실주문 전 **[SECURITY.md](SECURITY.md)** 체크리스트를 따르세요 (출금 불가 키, IP 화이트리스트, 키 재발급, 주문 한도).

Oracle 고정 IP를 Upbit API 키 허용 IP에 등록하세요.

### DESK 대시보드

토큰 로그인 + TradingView(`UPBIT:BTCKRW`) 상황 페이지.

```env
DASHBOARD_TOKEN=긴-랜덤-문자열
```

```bash
docker compose up -d --build
# http://<VPS-IP>:8080  (방화벽·보안목록에서 8080 개방)
```

`DASHBOARD_TOKEN`이 비어 있으면 대시보드는 전부 차단됩니다.

## Oracle VPS 배포 요약

1. Ubuntu에 Docker 설치  
   `curl -fsSL https://get.docker.com | sh && sudo usermod -aG docker $USER`
2. 재로그인 후 이 레포 clone
3. `cp .env.example .env` (`PAPER=true`)
4. `docker compose up -d --build`
5. `docker compose logs -f bot` 로 시그널/가상체결 확인

ARM(Ampere) 인스턴스도 `python:3.12-slim` 멀티아치로 동작합니다.

## 로컬 실행 (Docker 없이)

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux:   source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
set PAPER=true   # PowerShell: $env:PAPER="true"
python -m bot
```

## 백테스트

```bash
export PATH="$HOME/.local/bin:$PATH"
WRAPPER=.agents/skills/backtest/scripts/upbit-strategy-toolkit.sh

bash "$WRAPPER" strategy validate strategies/sma_cross_btc.json
bash "$WRAPPER" backtest run strategies/sma_cross_btc.json \
  --start 2025-07-26 --end 2026-07-26
```

> 페이퍼/백테스트 결과는 미래 수익을 보장하지 않습니다.  
> 실주문 전 PAPER로 충분히 검증하세요.
