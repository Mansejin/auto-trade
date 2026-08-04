# DESK UI 개선 노트

작성 기준: 2026-08 (듀얼 거래소 LIVE 운영, NAS + Cloudflare Tunnel)

공개 URL: `https://mansejin.com/autotrade`  
관련 코드: `web/app.py`, `web/static/index.html`, `web/static/desk.js`, `web/static/desk.css`

---

## 요약

Upbit 전용이던 대시보드를 **Upbit + Bitget 동시 표시**로 확장했고, Policy C **슬리브·스위치·자산** 패널을 같은 화면에 붙였다.  
USDT 잔고는 **소수 2자리**. 모바일은 1차 틱만 보이고 **더보기**로 2차 틱(UB/BG 시그널·포지션 등)을 펼친다.

---

## 1. 상단 티커 (듀얼 거래소 + 레짐)

현재 (`index.html` ticker-strip):

| 구역 | 항목 |
|------|------|
| 1차 | 레짐, CORE, 스위치, 리스크 (+ 더보기) |
| 2차 Upbit | UB시그널, 원화, UB포지션 |
| 2차 Bitget | BG시그널, USDT, BG포지션 |
| 기타 | SCALP, 이체(pending) |

- Bitget 현금은 API `bitget.cash` (`status.json` / `bitget_state.json` 병합).

---

## 2. 하단 패널

1. **Upbit 체결** — `state.json` trades 최근 8건  
2. **Bitget 체결** — `bitget_state.json` trades 최근 8건  
3. **슬리브 · 스위치** — `config/sleeves.json` + `regime-switch.jsonl` 이력  
4. **Upbit 상태** — `logs/latest_status.txt`  
5. **Bitget 상태** — `logs/bitget/latest_status.txt`  

자산 곡선은 상단 **자산** 링크 → `/equity`.


---

## 3. 금액 표시 (USDT 2자리)

`desk.js` `money()`:

- **KRW**: 원 단위 반올림 + `ko-KR` 로케일 + `원` 접미사  
- **USDT(및 기타 견적)**: 최대 **소수 2자리** (`en-US` 로케일)

수량(qty)은 기존처럼 최대 8자리 후 trailing zero 제거.

---

## 4. API (`GET /api/status`)

인증 세션 필요. 응답에 Bitget 블록 추가:

```json
{
  "ok": true,
  "stale": false,
  "status": { "...": "upbit 쪽 스냅샷" },
  "recent_trades": [],
  "latest_text": "...",
  "quote_currency": "KRW",
  "exchange": "upbit",
  "tv_symbol": "UPBIT:BTCKRW",
  "bitget": {
    "exchange": "bitget",
    "mode": "...",
    "strategy": "...",
    "market": "...",
    "cash": 9.83,
    "quote_currency": "USDT",
    "position": null,
    "signal": "hold",
    "latest_text": "...",
    "recent_trades": []
  }
}
```

데이터 경로(컨테이너 기본값):

| 용도 | 경로 |
|------|------|
| Upbit status | `LOG_DIR/status.json`, `latest_status.txt` |
| Upbit state/risk | `STATE_PATH`, `RISK_PATH` |
| Bitget status | `BITGET_LOG_DIR/status.json`, `latest_status.txt` |
| Bitget state | `BITGET_STATE_PATH` |

`stale`: 상태 파일 mtime이 900초(15분)보다 오래되면 true.

---

## 5. 차트

TradingView 위젯 유지.  
`tv_symbol` / `tv_interval`은 Upbit `KRW-*` → `UPBIT:…KRW`, Bitget USDT 마켓 → `BITGET:…USDT`로 매핑.

---

## 6. 운영·보안 (관련)

- `BASE_PATH=/autotrade` — Worker/터널 뒤에서 정적·API 경로 일치  
- 로그인: `DASHBOARD_TOKEN` + 세션 쿠키 (URL `?token=` 금지)  
- NAS 배포 시 desk는 Cloudflare Tunnel(`desk` alias)로만 공개; 호스트 `127.0.0.1:18080`은 LAN 디버그용

---

## 7. 체커 체크리스트

- [ ] 상단에 Upbit 원화·시그널과 Bitget USDT·시그널이 동시에 갱신되는가  
- [ ] USDT가 `9.8305`처럼 길게 나오지 않고 `9.83` 형태로 보이는가  
- [ ] 하단 4패널이 각각 최신 `latest_status` / 체결을 보여주는가  
- [ ] 한쪽 봇만 죽어도 다른 쪽 패널·티커가 비지 않는가(빈 값 `—`)  
- [ ] `/autotrade/healthz` 200, 로그인 후 `/api/status`에 `bitget` 키 존재

---

## 파일 맵

| 파일 | 역할 |
|------|------|
| `web/app.py` | status API, Bitget 병합, TV 심볼 |
| `web/static/index.html` | 듀얼 티커·4패널 마크업 |
| `web/static/desk.js` | 폴링 렌더, money/qty, 체결 이중 리스트 |
| `web/static/desk.css` | 패널·티커 레이아웃 |
| `web/static/login.html` | `BASE_PATH` 대응 로그인 |
