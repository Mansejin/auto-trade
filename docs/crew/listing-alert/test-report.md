# 상장 알림 MVP 검증 리포트 (T-014)

대상: `alerts/listing_alert.py`, `alerts/_selfcheck_listing.py`, `scripts/build_listing_alert_stats.py`,
`config/listing-alert-stats.json`, `docs/sales/upbit-listing-alert/templates.json` · 2026-10-08

## 실행

```
python -m alerts._test_listing_alert          # 새 테스트 (리플레이 2건은 실제 네트워크, LISTING_TEST_OFFLINE=1 이면 건너뜀)
python -m alerts._selfcheck_listing           # 기존 셀프체크
```

- `_test_listing_alert`: **22개 중 15개 통과, 7개 실패** (실패 7개는 모두 아래 버그 재현이고, 테스트 코드 오류는 아님)
- `_selfcheck_listing`: OK
- 테스트는 매번 임시 `BOT_ROOT`를 쓴다. 통계 재생성 검사는 실행 후 `config/listing-alert-stats.json` 원본 바이트를 되돌려 놓는다.

## 통과한 항목

- 리플레이(실제 API): NMR(6642) → Binance NMRUSDT 분포 알림. CASHCAT(6618) → Binance 없음·Bybit CASHCATUSDT, 분포 없는 알림. POD(6635) → 해외 무기한 없음. 세 건 모두 고지 문구 포함, 금지어 없음, 치환 안 된 `{변수}` 없음, 기록 파일은 쓰지 않음.
- 실제 `seven_day`(LIT, LITUSDT)가 4.8%로 통계 원본 CSV 계산값과 같다. 통계와 7일 회신이 같은 가격 정의(D+1 시가 → D+8 시가)를 쓴다.
- 첫 실행(bootstrap)은 이미 있던 공지를 발송하지 않는다.
- 운영 중 공지 API가 실패하면 `source_down`을 1줄만 남기고 죽지 않는다. 그 사이 신규 마켓은 market/all 비교로 1회 알린다. API가 복구된 뒤 같은 공지가 다시 와도 중복 알림이 없고, `source_recovered`는 1줄 남는다.
- 같은 공지 id가 두 번 오거나 같은 티커의 변경 공지가 와도 알림은 1건이다.
- 무기한 없음: `alert_no_perp` 문구("집계에서 제외" 포함), 과거 분포 수치 없음, 7일 회신 없음, 누적 집계에서 제외(`누적 1건`).
- 1000XXX 매핑(1000BONK, 1000SATS)이 맞고, 알림 시각 이후 상장한 무기한은 제외한다. 거래대금·펀딩 반올림도 맞다.
- 회신 시각은 정확히 D+8 00:10 UTC이고 1초 전에는 대상이 아니다. D+8 일봉이 없으면 None을 돌려준다. 고가는 D+1~D+7만 본다.
- 재시작: 상태 파일을 다시 읽어도 재발송하지 않고 7일 회신도 1건만 나간다. 상태 파일이 없어져도 bootstrap 기록만 남기고 재발송하지 않는다.
- jsonl은 덧붙이기만 한다. 매 폴링 뒤 이전 바이트가 새 파일의 앞부분과 정확히 같은지 확인했다.
- DRY_RUN에서는 `TelegramNotifier`를 아예 생성하지 않는다(생성하면 예외가 나도록 막아 두고 확인). 기록은 `dry_run=true, sent=false`.
- `templates.json`이 없거나 JSON이 깨져도 FALLBACK으로 보내고, 세 종류 모두 고지 문구를 넣는다. 고지 문구가 빠진 템플릿에는 끝에 붙인다.
- 금지어: `templates.json`과 FALLBACK 모두 금지어가 없고 "매수/매도"도 없다. 금지어가 든 템플릿은 FALLBACK으로 바뀐다. 기록된 모든 메시지에 고지 문구가 있다.
- `scripts/build_listing_alert_stats.py`를 다시 돌리면 `config/listing-alert-stats.json`과 같은 값이 나온다(n=133, p10/50/90 −32.9/−11.2/+12.2).
- "하락" 판정(ret<0)이 통계 원본과 7일 회신 규칙에서 같은 결과(93/133)를 낸다.

## 발견한 버그

| # | 심각도 | 증상 | 재현(테스트 이름) | 파일 | 담당 |
|---|---|---|---|---|---|
| B1 | Major | Binance API 장애(exchangeInfo 실패)도 "Binance 없음" + "과거 표본에 해당하지 않아"로 발송한다. 7일 회신·집계에서 영구 제외되고, 공개 기록에는 사실과 다른 문구가 남는다. | `Binance lookup failure is not reported as 'perp absent'` | `listing_alert.py` `snapshot`/`build_alert` (`binance_error`를 무시함) | backend |
| B2 | Major | `DRY_RUN`에서 LIVE로 바꾸면, dry-run으로만 기록된 알림의 7일 회신이 실제 채널로 나간다. 원 알림은 공개된 적이 없고 `#번호`도 맞지 않는다. `due_followups`가 `dry_run`을 거르지 않는다. | `DRY_RUN -> LIVE switch ...` | `due_followups` | backend |
| B3 | Minor~Major | 상태 파일을 `run_once` 끝에서만 저장한다. 알림을 기록한 뒤 상태를 저장하기 전에 프로세스가 죽으면(docker restart, 회신 단계 예외) 다음 폴링에서 같은 공지를 다시 발송한다. | `kill between alert append and state save` (run_followups가 예외를 내게 해서 재현, 알림 2건) | `run_once` | backend |
| B4 | Minor | bootstrap 중 공지 API가 실패하면 폴링마다 `source_down`이 1줄씩 쌓인다(3회 실패 → 3줄). 상태를 저장하지 않아 `down` 플래그가 사라지기 때문이다. 이 줄들은 `fwd_missed_n`에도 더해진다. | `notice API failure during bootstrap` | `run_once` 앞부분 | backend |
| B5 | Minor | `fwd_missed_n`("누락·오류")이 `source_down` 줄을 모두 센다. 알림 누락이 없었던 market/all 장애도 누락 1건으로 공개된다. | `fwd_missed_n counts only missed alerts...` | `followup_vars` | backend (정의는 lead 확인) |
| B6 | Minor | 7일 회신은 반올림한 `ret_7d_pct < 0`으로 하락을 센다. 실제 −0.04%가 −0.0이 되어 하락에서 빠진다. 통계 원본은 반올림 전 값으로 센다. 과거 133건에서는 차이가 없지만 정의가 다르다. | `'fell' tally edge: -0.04%` | `followup_vars`/`seven_day` | backend |
| B7 | Doc | 공개 기준값 "단순 가격 89/133 하락"(보드 T-016 팀장 결정, `community-posts.md`, `message-templates.md`)이 실제 가격 정의(D+1 시가 → D+8 시가)와 다르다. 이 정의로 다시 세면 **93/133 (69.9%)**이다. 89는 리서치 카드의 `gross > 0` 값으로, 다른 정의다. | `published baseline '89/133 fell'...` | docs/sales, `.crew/board.md` | lead / sales-marketer |

참고(실패 테스트 없음): 공지 제목이나 티커에 금지어가 들어 있으면 FALLBACK도 금지어를 포함하게 된다. 이때 `AssertionError`로 `alert_error`가 기록되고, 그 공지는 seen 처리되어 다시 알리지 않는다. 실제 업비트 제목에서는 일어나기 어렵다.

## 커버하지 못한 영역

- LIVE 텔레그램 실제 발송, 전송 실패(`sent=false`) 후 재시도 정책(현재는 재시도 없음).
- 실제 업비트 공지 API 응답 형식 변화. 공지 1페이지(20건)를 넘는 다수 동시 공지.
- 리플레이는 현재 시점 Binance 정보(거래대금·펀딩·exchangeInfo)를 쓴다. 과거 시점 값과는 다르다.
- 상장일 D 정의 차이: 리서치는 업비트 KRW 첫 일봉 날짜를 쓰고, 알림은 공지 시각의 KST 날짜를 쓴다. 공지 다음 날 거래를 시작하는 경우는 검증하지 않았다.
- 같은 티커가 상폐 후 재상장하면 `tickers` 집합 때문에 영구히 알림이 막힌다(설계 확인 필요, 테스트 없음).
- Bybit/Bitget 조회 실패 시 "확인 실패" 표기의 실제 API 경로.
