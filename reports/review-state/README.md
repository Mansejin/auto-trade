# review-state (AI)

**읽기 순서(저토큰):** `{slug}.json` 1개만. CSV는 거래 디테일 필요할 때만.

| 키 | 용도 |
|---|---|
| `logic` | 현재 buy/sell/risk 규칙 |
| `scoreboard` | filt vs base 한눈 비교 |
| `trades_f` / `gap` | 체결·놓친 기회 |
| `diag` | 로직 병목 진단 |
| `levers` | 임계값 조정 맵 |
| `next_candidates_precomputed` | 보고 후 바로 꺼낼 수정안 |
| `revise_flow` | 보고→제안→v2→재측정 |

트리거: 사용자 **보고** → 사실 보고 → `auto_propose_after_report`면 후보 자동 제안.
