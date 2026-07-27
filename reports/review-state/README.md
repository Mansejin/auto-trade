# Review State

이 폴더는 백테스트 비교·임계값 수정 제안용 상태 파일입니다.

## 사용법
1. 사용자가 **보고**를 지시하면 `reports/review-state/{slug}.json` + 최신 CSV로 사실 보고
2. 보고 직후 `revision_playbook` / `proposal_rules`에 따라 임계값 수정안 1~3개 자동 제안
3. 승인 시 `create-strategy`로 `-v2` 저장 → validate → backtest

## 현재 활성
- `sma-5-20-golden-cross-filtered.json` (`auto_propose_after_report: true`)
