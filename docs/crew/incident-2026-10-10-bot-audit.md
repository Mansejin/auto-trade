# 사고 점검 보고서 — NAS 봇 스택 (2026-10-10)

- 점검 시각: 2026-10-10 00:53~00:56 KST, 읽기 전용 (재시작·설정 변경·주문 없음)
- 대상: `ssh nas` → `/volume1/docker/p3f8c1a2`, 컨테이너 w1~w6
- 시간 표기: DB·docker 타임스탬프는 UTC, 봇 로그 본문은 KST(+9). 표 안에 따로 적음.
- 점검 스크립트(읽기 전용, 커밋 안 함): `deploy/nas/_audit_incident_a.sh`, `_audit_incident_b.sh`, `_audit_incident_c.sh`, `_audit_incident_w5db.py`, `_audit_incident_w5log.sh`, `_audit_incident_w5lev.py`

## 요약

w5의 손실 거래 4건(trade 2~5)은 **손절로 닫힌 게 아니라 거래소 강제청산**이었다. 청산가는 기록된 `liquidation_price`와 거의 같고, 손실액은 20배 격리 증거금 전액과 같다. 원인은 두 가지가 겹친 것이다.

1. 레버리지 설정이 **교차(crossed) 마진 설정에만 3배로 들어갔고**, 실제 포지션은 **격리(isolated) 마진 기본값 20배**로 열렸다.
2. 패치된 거래소 손절(트리거 주문)이 `marginMode` 없이 나가서 **crossed 주문으로 등록**됐다. 가격이 트리거에 닿으면 줄일 crossed 포지션이 없어서 거래소가 `status=failed`로 처리했다. 그런데 봇의 `_fetch_stoploss_order`는 "대기 목록에 없음"을 "closed"로 해석했고, 그래서 손절을 계속 다시 걸다가 결국 청산당했다.

이 문제는 계정이 원래부터 UTA였으므로 **첫 거래(8/6)부터 계속** 있었다. "중간에 UTA로 바뀐 시점"은 없다.

---

## w5 — freqtrade (LIVE, Bitget BTC/USDT:USDT 숏, TrendShortV1Lev3Px)

상태: running, 시작 2026-10-09 15:53:35 UTC(팀장 재시작), RestartCount 0, 헬스체크 없음. DB 기준 열린 거래는 trade 6 (숏 0.0002 @ 86,392.7, 오픈 2026-09-21 22:45 UTC).

거래소 실측 (00:55 KST): 숏 0.0002, 진입 86,392.7, 마크 82,807.4, **레버리지 20, isolated**, 청산가 90,678.5, 개시증거금 0.864 USDT, 미실현 +0.72. 계정 자산 6.96 USDT (가용 USDT 5.31). 대기 트리거 주문 0건, 대기 일반 주문 0건이라 고아 손절 주문은 없다.

`privateUtaGetV3AccountSettings`: `accountMode=unified`, `holdMode=one_way_mode`, BTCUSDT `symbolConfigList` = `[crossed leverage=3]`, `[isolated leverage=20 (long/short 20)]`.

| 심각도 | 증상 | 증거(타임스탬프) | 추정 원인 | 권장 조치 | 담당 |
|---|---|---|---|---|---|
| critical | 손실 거래 2~5가 손절이 아니라 강제청산으로 닫힘 | DB 청산가와 liquidation_price 비교: T2 67,685.1 / 67,565.8 (8/19 15:27 UTC), T3 72,344.9 / 72,334.4 (8/20 10:15), T4 81,909.9 / 81,896.9 (9/3 21:30), T5 84,871.6 / 84,871.3 (9/21 09:38). 손절가(+3%)를 1.4~1.7% 지나서 체결. 손실 -0.75~-1.02 USDT는 20배 격리 증거금(명목가÷20)과 같음 | 아래 두 행의 결과 | 아래 두 건을 고치기 전까지 새 진입 금지(`/stopentry` 또는 max_open_trades=0) | 팀장 결정 → backend-dev |
| critical | 거래소 손절 트리거가 발동 직후 실패함 | `privateUtaGetV3TradeHistoryStrategyOrders`: T5 트리거 1485849392200532070, 1485849454624358438, 1485850524935241789 모두 `status=failed`, **`marginMode=crossed`**, triggerPrice 83,503.6 (실패 시각 2026-09-21 08:40~08:46 UTC). DB에는 같은 거래에 손절이 9번 다시 걸림. T2(8/19 15:13~15:19, 9개), T3(8/20 08:17~08:38, 8개), T4(9/3 15:01~16:45, 33개)도 같은 패턴 | `TrendShortV1._uta_trigger_body`에 `marginMode`가 없어서 UTA 기본값 crossed로 등록됨. crossed 포지션이 없으니 reduceOnly 트리거가 실패함. 또 `_fetch_stoploss_order`는 대기 목록에 없는 주문을 `closed`로 반환해서 freqtrade가 "손절 체결"로 착각하고(exit_reason=stoploss_on_exchange) 다시 거는 루프를 돎 | ① 트리거 바디에 `marginMode: "isolated"` 추가 (UTA가 이 파라미터를 받는지 **미확인**, 소액으로 검증 필요). ② `_fetch_stoploss_order`가 history를 조회해서 failed/cancelled를 `canceled`로, 실제 체결만 `closed`로 반환하게 수정. 그 전까지는 현재 설정(stoploss_on_exchange=false) 유지 | backend-dev (+ qa-tester 소액 검증) |
| critical | 거래소 레버리지 20배인데 freqtrade는 3배로 기록 | 계정 설정 crossed=3, isolated=20. 포지션 leverage 20.0. DB T2~T6 leverage 3.0. 청산가 차이 T6 +4.4~5.0% ≈ 20배 | freqtrade `_set_leverage` → ccxt `set_leverage(symbol, 3)` 호출에 `marginMode`/`posSide`가 없음(ccxt docstring: "posSide required for uta isolated margin"). 그래서 UTA가 crossed 설정만 3으로 바꿨고, 주문은 isolated로 나가서 기본값 20배가 적용됨. 호출 자체는 에러 없이 성공해서 로그에도 남지 않음. 진입 시점(9/21) 로그는 로테이션으로 사라져서 **로그상 직접 확인은 미확인**(계정 설정값으로 추론) | `set_leverage`를 `params={"marginMode":"isolated"}`(필요하면 `posSide`)로 호출하도록 bot_start 패치 추가, 또는 거래소 UI에서 BTCUSDT isolated 레버리지를 3으로 수동 설정. 기존 포지션에는 적용 안 될 수 있음(**미확인**) | backend-dev / 사용자(UI 수동 설정) |
| high | 현재 손절이 소프트웨어 방식뿐이라 봇이 멈추면 보호가 없음 | 2026-10-07 00:06:51 KST `Fatal exception` (ConnectionResetError) 발생 후 재시작까지 12초 걸림. 2026-10-06 14:31 KST `fetch_positions NetworkError` | 네트워크 예외로 프로세스가 죽음. restart 정책으로 복구는 됐음. 지금은 20배라 청산가가 진입가 +5.0%, 소프트 손절은 +3.0% (88,984.4) | 레버리지를 3배로 고치면(위 행) 청산 여유가 약 +33%로 늘어나서 다운타임 리스크가 크게 줄어듦. 그 전까지는 Bitget 앱에서 포지션 TP/SL을 수동으로 걸어 두는 것을 검토 | 사용자 / 팀장 |
| medium | 5초마다 fee 업데이트 루프 (하루 약 16,600줄) | 2026-09-30 이후 모든 로그 파일에 하루 16,632회 반복. `Updating buy-fee on trade Trade(id=1 ... open_since=closed) for order 1469100821086462031` → `myTrade-dict empty found` | trade 1(8/6, leverage 1)은 청산 주문 없이 닫혔고(close_rate=None) 손절 주문 1469100821086462031은 실제 체결이 없음. freqtrade `update_trades_without_assigned_fees`가 trade 1의 close fee가 비어 있어서 매 루프마다 체결 내역을 조회하는데, 결과가 비어 있으니 끝없이 반복됨 | 봇 정지 → DB 백업 → trade 1에 `fee_close=0, fee_close_cost=0, fee_close_currency='USDT'` 설정 (또는 trade 1 삭제) → 재시작 | 팀장 (DB 작업) |
| medium | 로그 스팸 때문에 포렌식 증거가 사라짐 | logfile 10MB×11개가 약 10일치(9/30 04:08~). docker 로그는 10/07 06:19 UTC부터만 남음. trade 6 진입(9/21) 시점의 레버리지·손절 로그 없음 | 위 fee 루프 | fee 루프를 고치면 해결됨. 필요하면 `--logfile` 로테이션 수를 늘림 | devops |
| medium | w2와 같은 API 키·계정·심볼을 씀 | 사용자 제공 정보. w2 코드에 `foreign_position` 가드 있음(`bot/bitget_runner.py` 366~373) | 공유 계정이라 one-way 모드에서 포지션이 상계될 수 있음. w5는 `stake_amount=unlimited`, `tradable_balance_ratio=0.99`라서 잔고를 사실상 전부 씀 | w2를 LIVE로 바꾸기 전에 서브계정이나 별도 키로 분리 | 사용자 / devops |
| low | `fetch_leverage` 40085 | `ccxt.fetch_leverage` → `40085 Unified Account mode, Classic API not supported` | ccxt 4.5.68의 fetch_leverage가 UTA 경로를 지원하지 않음. 진단용 코드만 영향 | 진단할 때 `privateUtaGetV3AccountSettings`를 사용 | — |

DB 정리 확인: trade 6 손절 주문 1486065525176377361 (2026-10-09 15:51:46 UTC canceled), 1492481026454708224 (10/09 15:52:06에 생성 → 15:53:26 canceled). 거래소 대기 트리거가 0건이라 실제 고아 주문은 없다. 백업 파일 2개(`.bak-20261009155153`, `.bak-20261009155333`)도 확인했다.

"UTA 전환 시점" 질문: trade 1(8/6)부터 이미 격리 20배 청산가 패턴(진입 64,495.6 / 청산가 67,329.2, +4.4%)이 보이고, 전략 파일(8/6 작성)도 40085를 전제로 한다. 따라서 **trade 2~5와 trade 6 사이에 UTA가 바뀐 것은 아니다.** trade 2~5의 손절도 똑같이 실패했다. 차이는 trade 6이 아직 손절가에 닿지 않았다는 것뿐이다.

---

## w1 — Upbit 봇 (LIVE, SMA200 1d)

상태: running, 시작 2026-10-08 08:45:34 UTC, RestartCount 0, healthy.

| 심각도 | 증상 | 증거 | 추정 원인 | 권장 조치 | 담당 |
|---|---|---|---|---|---|
| high (기회손실) | 매수 신호인데 돈이 없어서 포지션이 비어 있음 | `status.json` signal=buy, krw=22.75, base_qty=0, equity 22.75원. 2026-10-08 17:45 KST 이후 5분마다 `LIVE BUY SKIP ... reason=min_order` (7일간 372회) | KRW 잔고 23원. 돈이 어디로 갔는지는 **미확인**(.env `TRANSFER_ENABLED=true`, Bitget 쪽 자산도 6.96 USDT뿐) | 운영 의도를 확인(전략을 계속 돌릴지). 계속 돌린다면 입금 | 사용자 |
| medium | 잔고 부족을 알리지 않음 | 코드상 WARNING 로그 + trades.log만 남기고 return 함(`bot/main.py` 424~439). 에러 루프나 연속 오류 카운트 증가는 없고(`record_success`), 다음 틱에 다시 시도함. 텔레그램 호출 로그 없음(httpx 로깅 여부 때문에 **미확인**) | 설계상 조용히 넘어감 | 같은 bar_key당 텔레그램 알림 1회 추가 | backend-dev |
| low | 하루 288줄 WARNING 스팸 | 위와 같음 | 같음 | 알림을 추가하면 로그 레벨을 INFO로 낮춤 | backend-dev |
| low | 간헐적 DNS 실패 | `httpx.ConnectError: Name or service not known` 2026-10-09 00:51:29, 21:48:54 KST, 다음 틱에 복구 | NAS·도커 DNS 일시 장애 | 반복되면 compose에 `dns:` 지정 | devops |

---

## w2 — Bitget 봇 (PAPER, SMA cross 1h)

상태: running, 시작 2026-08-20 15:20 UTC, RestartCount 0, healthy. `.env` `BITGET_PAPER=true`, `BITGET_STRATEGY_PATH`가 비어 있어서 기본값 `bitget_btc_usdt_sma.json`을 씀.

| 심각도 | 증상 | 증거 | 추정 원인 | 권장 조치 | 담당 |
|---|---|---|---|---|---|
| medium (잠재) | PAPER인데 전략에 `funding.enabled=true`(Upbit KRW→TRX 자동 브리지), `.env`는 `TRANSFER_ENABLED=true`. 전략 이름도 "LIVE + TRX bridge fund" | strategies/bitget_btc_usdt_sma.json. PAPER 경로는 funding 전에 return 하므로(`bitget_runner.py` 123, 293) **지금은 실제 이체 없음** | PAPER를 false로 바꾸는 순간 w5와 같은 계정에서 실주문과 자동 이체가 동시에 켜짐 | LIVE 전환 전에 계정 분리 + funding 끄기 결정 | 사용자 / 팀장 |
| low | 간헐적 DNS 실패 1회 | 2026-10-03 02:06:44 KST `ConnectError` | w1과 같음 | w1과 같음 | devops |
| low | 상태 파일 권한 | `data/bitget_state.json` NAS 사용자로 읽기 Permission denied (root 소유로 추정) | user 0:0으로 실행해서 | 점검에만 불편함. 조치 불필요 | — |

로그상 PAPER BUY/SELL은 정상(7일간 매수·매도 각 6회 남짓).

---

## w3 — desk 대시보드

| 심각도 | 증상 | 증거 | 추정 원인 | 권장 조치 | 담당 |
|---|---|---|---|---|---|
| low | `.env` 경로 스캐닝 시도 | `GET /v1/.env`, `/svelte/.env`, `/resources/.env` → 404 (7일간 각 1회) | 인터넷 봇 스캔 | 이미 404라 조치 불필요. 필요하면 Cloudflare WAF 규칙 추가 | — |

상태: running(8/20부터), RestartCount 0, healthy, `/healthz` 200 연속, 에러 0.

---

## w4 — cloudflared

| 심각도 | 증상 | 증거 | 추정 원인 | 권장 조치 | 담당 |
|---|---|---|---|---|---|
| low | QUIC 연결이 잠깐씩 끊김 | 2026-10-02 22:11, 10-03 19:18, 10-08 17:04 UTC `timeout: no recent network activity` → 2~8초 안에 재등록 | 망 일시 장애. 4개 연결 중 1개만 끊겨서 서비스 영향은 없었을 것으로 보임 | 조치 불필요 | — |
| low | 버전이 오래됨 | `Your version 2026.6.1 is outdated ... 2026.10.0` (매일) | compose는 `:latest`인데 이미지를 8/4 이후로 pull하지 않음 | 날짜 태그로 고정한 뒤 pull·재생성 | devops |

---

## w6 — Upbit 상장 알림

상태: running, 시작 2026-10-08 10:09:55 UTC, `dry_run=False`, 3분 주기 폴링.

| 심각도 | 증상 | 증거 | 추정 원인 | 권장 조치 | 담당 |
|---|---|---|---|---|---|
| low | DNS 실패 1회 | 2026-10-08 21:58:49 KST `net error ConnectError ... retry in 1s` 후 정상 | w1과 같음 | — | — |
| 정상 | 텔레그램 발송 성공 | 2026-10-09 17:23:28 KST KAIA 감지 → 바이낸스·바이빗·비트겟 조회 → `sendMessage 200 OK`. 실패 기록 없음 | — | — | — |

---

## 다음 작업 제안 (보드용)

- to: backend-dev — `TrendShortV1.py`: 트리거 바디에 `marginMode` 추가, `_fetch_stoploss_order`가 history로 failed/cancelled와 실제 체결을 구분하게 수정, bot_start에서 `set_leverage(..., params={"marginMode":"isolated"})` 패치. 소액 실검증 후 stoploss_on_exchange를 다시 켤지 결정.
- to: 팀장 — trade 1 fee 필드 DB 정리(정지 → 백업 → 수정 → 재시작). 레버리지를 고치기 전 신규 진입을 막을지 결정.
- to: 사용자 — Bitget에서 BTCUSDT isolated 레버리지를 3으로 바꿀지, w1 KRW 잔고(23원)를 어떻게 할지 결정.
