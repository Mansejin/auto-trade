# review-state (AI)

**읽기 순서(저토큰):** `ACTIVE` → 그 JSON만. CSV는 거래 디테일 필요할 때만.

## 기간/타임스탬프 (필수)
모든 비교 백테스트는 **동일 구간**:
- **start:** `2025-07-26` (UTC 00:00)
- **end:** `2026-07-26` (UTC 00:00)
- **timeframe:** `1d`
- **선정:** `1d` 기본값 = 최근 1년, end = 실행일 기준 UTC yesterday

CSV 파일명의 `YYYYMMDD_HHMMSS` = **실행 시각(UTC)**.  
예: `...-20260727_163119.csv` → 2026-07-27 16:31:19 UTC 실행.

상세는 각 slug JSON의 `WINDOW` / `RUNS` 키.

| 키 | 용도 |
|---|---|
| `WINDOW` | 백테스트 캔들 구간 (start/end/tz/bars) |
| `RUNS` | 버전별 CSV + 실행 UTC/KST |
| `logic` | 현재 buy/sell/risk |
| `scoreboard` | 버전 비교 |
| `diag` / `levers` / `next_candidates_*` | 수정용 |

트리거: 사용자 **보고** → 사실 보고(기간 먼저) → 후보 자동 제안.
