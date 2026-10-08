# 메시지 템플릿: 업비트 상장 이벤트 알림

> 2026-10-08 · sales-marketer · 보드 T-011 · 코드용 원본은 `templates.json`(키: `alert`, `alert_no_perp`, `followup`)
> 근거: `docs/product/upbit-listing-alert-brief.md` 3절(알림 내용), `docs/research/redteam/upbit-listing-fade.md`

## 공통 규칙 (앱개발)
- 텔레그램 **일반 텍스트**로 보낸다(parse_mode 없음). 마크다운 이스케이프 문제를 피한다. `bot/telegram_notify.py`의 `send(text)` 그대로 사용 가능.
- 치환은 Python `str.format(**vars)`. 값이 없으면 `-`로 채운다. 빈칸으로 두지 않는다.
- 숫자 형식: 퍼센트는 부호 포함 소수 1자리(`-9.1`, `+15.0`), 펀딩만 소수 4자리(`+0.0100`). 거래대금은 `12.3M` / `850K` 형식(USD).
- 매수·매도·진입·목표가 표현을 코드에서 덧붙이지 않는다. 템플릿 밖 문장 추가 금지.
- 마지막 고지 줄은 **절대 생략하지 않는다.** 법무 T-010의 `disclaimer-draft.md`가 확정되면 그 문구로 바꾼다(줄 수는 1~2줄 유지).
- 길이: 모바일 한 화면(약 15줄, 600자 이하)을 목표로 했다.

## 1. 알림 `alert` (해외 무기한이 1곳 이상 있을 때)

```text
[상장 이벤트 #{alert_id}] {ticker}
공지: {notice_title}
시각: {notice_time_kst} KST
원문: {notice_url}

해외 무기한: Binance {perp_binance} / Bybit {perp_bybit} / Bitget {perp_bitget}
무기한 상장 {perp_age_days}일째 · 24h 거래대금 ${quote_volume_24h} · 펀딩 {funding_rate_pct}% ({funding_source})

과거 비슷한 상장 {hist_n}건, 다음 날부터 7일 가격 변화
하위10% {hist_p10_pct}% · 중앙 {hist_p50_pct}% · 상위10% {hist_p90_pct}%
7일 안에 +30% 이상 오른 경우: {hist_up30_share_pct}%

7일 뒤 결과를 이 채널에 그대로 남깁니다.
※ 과거 분포일 뿐 이 코인의 결과를 예측하지 않습니다. 투자 권유 아님, 원금 손실 가능.
```

## 2. 알림 `alert_no_perp` (3개 거래소 모두 무기한 없음)

```text
[상장 이벤트 #{alert_id}] {ticker}
공지: {notice_title}
시각: {notice_time_kst} KST
원문: {notice_url}

해외 무기한: Binance 없음 / Bybit 없음 / Bitget 없음
→ 과거 표본(해외 무기한이 이미 있던 상장)에 해당하지 않아 분포를 붙이지 않습니다.
이 건은 기록만 하고 7일 결과 집계에서 제외합니다.

※ 과거 분포일 뿐 이 코인의 결과를 예측하지 않습니다. 투자 권유 아님, 원금 손실 가능.
```

## 3. 7일 결과 `followup`

```text
[7일 결과 #{alert_id}] {ticker}
원 알림: {alert_sent_kst} KST 발송
{entry_date} 시가 → {exit_date} 시가 (UTC 일봉): {ret_7d_pct}%
과거 중앙값 {hist_p50_pct}% 대비 {ret_vs_median_pp}%p

공개 기록 누적 {fwd_n}건: 하락 {fwd_fell_n}건 ({fwd_fell_share_pct}%)
누락·오류 {fwd_missed_n}건 포함 전체 기록: {record_url}

※ 과거 분포일 뿐 이 코인의 결과를 예측하지 않습니다. 투자 권유 아님, 원금 손실 가능.
```

## 4. 변수 매핑 (MVP 데이터와 1:1)

| 변수 | 의미 | 출처·계산 | 예시 |
|---|---|---|---|
| `alert_id` | 알림 일련번호(공개 기록의 행 번호와 동일) | append-only 기록의 다음 번호 | `7` |
| `ticker` | 티커 | 공지 파싱(`fetch_upbit_announcements.py`) | `ABC` |
| `notice_title` | 공지 제목 원문 | 공지 파싱 | `[거래] ABC(ABC) 원화 마켓 디지털 자산 추가` |
| `notice_time_kst` | 공지 게시 시각 | 공지 파싱, `YYYY-MM-DD HH:MM` | `2026-10-08 16:31` |
| `notice_url` | 공지 원문 링크 | 공지 파싱 | |
| `perp_binance` / `perp_bybit` / `perp_bitget` | 무기한 존재 여부 | 거래소 심볼 조회(`build_listing_perp_map.py` 규칙, 1000XXX 포함) → `있음`/`없음` | `있음` |
| `perp_age_days` | 무기한 상장 후 경과일 | 존재하는 거래소 중 **가장 오래된** 무기한 첫 일봉 기준 | `412` |
| `quote_volume_24h` | 24h 거래대금(USD) | 위와 같은 거래소의 24h ticker quoteVolume | `38.2M` |
| `funding_rate_pct` | 현재 펀딩비(정산 1회분) | 같은 거래소 현재 펀딩, ×100 | `+0.0100` |
| `funding_source` | 펀딩·거래대금을 가져온 거래소 | 우선순위 Binance → Bybit → Bitget | `Binance` |
| `hist_n` | 과거 표본 수 | 고정 `133` (OOS 상장일 2023-07~2026-09) | `133` |
| `hist_p10_pct` / `hist_p50_pct` / `hist_p90_pct` | 과거 7일 가격 변화 분위수 | `reports/research-cards/upbit-listing-fade.json`의 `events` 중 `listing >= 2023-07-01`, 값 = `-gross × 100`(비용·펀딩 제외 가격 변화). 2026-10-08 계산값 `-28.2` / `-9.1` / `+15.0`. 시작 시 1회 계산해 고정 | `-9.1` |
| `hist_up30_share_pct` | 보유 7일 중 고가 기준 +30% 이상 오른 비율 | 고정 `14.3` (19/133, 레드팀 보고서 3절) | `14.3` |
| `alert_sent_kst` | 원 알림 발송 시각 | 기록의 발송 시각 | |
| `entry_date` / `exit_date` | 측정 구간 | 공지+24h 이후 첫 UTC 일봉 시가 → 7일 뒤 시가(백테스트와 같은 정의) | `2026-10-10` |
| `ret_7d_pct` | 실제 7일 가격 변화 | `funding_source` 거래소 무기한 일봉 시가 기준 | `-12.4` |
| `ret_vs_median_pp` | 중앙값 대비 차이 | `ret_7d_pct - hist_p50_pct` | `-3.3` |
| `fwd_n` | 결과가 나온 포워드 알림 누적 수 | 기록에서 `alert`(무기한 있음) 중 결과 확정 건 | `5` |
| `fwd_fell_n` / `fwd_fell_share_pct` | 그중 `ret_7d_pct < 0` 건수·비율 | 기록 집계 | `3` / `60.0` |
| `fwd_missed_n` | 공지 수집 실패·발송 누락 등 | 기록의 `missed` 행 수 | `0` |
| `record_url` | 공개 append-only 기록 주소 | env 설정(페이지 확정 전엔 `-`) | |

### 정의 메모
- 분포·포워드 집계 모두 **비용·펀딩을 뺀 가격 변화**로 통일했다(알림 독자는 현물 보유자·추격 매수 고민자). 백테스트의 "비용·펀딩 포함 하락 63.9%"와 숫자가 다르다(가격만 보면 93/133 = 69.9%, Binance 무기한 D+1 시가→D+8 시가). 유료화 중단 기준(포워드 하락 비율 < 50%)도 같은 가격 정의로 잰다(팀장 결정 2026-10-08).
- 승률처럼 보이지 않도록 하락 비율은 **포워드 누적 집계에만** 쓰고, 알림 본문에는 분위수 3개와 +30% 역행 비율을 함께 둔다.
- `alert_no_perp` 건은 `fwd_n`에 넣지 않지만 공개 기록에는 남긴다.
