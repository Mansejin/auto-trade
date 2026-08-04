# Alpha / Regime Handoff — Local Agent Continuation

> **Updated:** 2026-07-29T06:03Z  
> **Purpose:** Cloud agent → local agent 이관용. MCP/환경 제약으로 로컬에서 전략 디벨롭을 이어갈 때 **이 파일 + 아래 프롬프트**만으로 재개 가능해야 함.  
> **Not investment advice.** LIVE 승격은 사람 승인 + audit 게이트 필수.

---

## 0. 60초 요약

| 항목 | 상태 |
|------|------|
| Goal | Policy C 유지하면서 **직교 alpha** 찾기. Overfit 금지. |
| LIVE / Policy C | **변경 없음.** Bear → `m5-v6`. Map 그대로. |
| TA scrapes AE6–AE11 | 전부 falsified / untestable. **재개 금지.** |
| Research shelf | (1) funding H1 `≤ -0.0002` (2) Upbit rich-premium fade |
| Open | **AE14** paper-log done; H2 OB pending. **AE15** Bitget basis hyp registered (unscored). 컷 재탐색 금지. |
| Branch | `cursor/alpha-ae6-flush-fade-d7d9` (base: `cursor/regime-ops-guards-d7d9`) |
| PR | https://github.com/Mansejin/auto-trade/pull/9 |

---

## 1. Git / PR 지도

```
main
  └─ (regime feature may live elsewhere; ops guards not on main)
       └─ cursor/regime-ops-guards-d7d9     ← PR #6 ops guards
            └─ cursor/alpha-ae6-flush-fade-d7d9  ← PR #9 alpha track (현재 작업선)
```

**로컬에서:**

```bash
git fetch origin
git checkout cursor/alpha-ae6-flush-fade-d7d9
git pull origin cursor/alpha-ae6-flush-fade-d7d9
```

Ops(closed-bar / dwell / position guard)는 base branch `cursor/regime-ops-guards-d7d9`에 있음. Alpha 작업은 PR #9 선에서 이어가면 됨.

---

## 2. LIVE / Policy C (건드리지 말 것)

| Key | Value |
|-----|--------|
| Current regime (labels) | bear (as of engine snapshot ~2026-07-27) |
| LIVE strategy | `strategies/krw-btc-1h-ema-adx23-rsi55-sl3-tp45-m5-v6.json` |
| Policy C map | bull→bull-v2, bear→m5-v6, sideways→sw-v5, transition→bull-v2 |
| Caps | `MAX_ORDER_KRW=15000`, `MAX_DAILY_LOSS_KRW=5000` |
| Lag cost (AE12) | risk-off 7d median BTC MDD **−5.45%**, worst **≈ −15.5%** → 사이즈 근거, SMA 버퍼 금지 |

State file: `reports/review-state/regime-engine.json`  
Playbook: `docs/regime-auto-switch-playbook.md`

### Ops (VPS에 아직 배포 필요할 수 있음)

- Closed daily bar classify
- Hard dwell 24h after `action=switched`
- Cancel open KRW-BTC orders; BTC position > dust → `position_skip` (자동 청산 없음)
- Script: `scripts/remote_regime_switch.py`
- Log: `logs/regime-switch.log`
- **거부한 Gemini 제안:** cron만 바꾸기 / transition→sideways / ±3% SMA / switch 시 market-sell

---

## 3. Alpha track 성적표 (AE6–AE13)

| ID | Idea | Verdict | Report |
|----|------|---------|--------|
| AE6 | 4h MFI+Williams flush fade | **Falsified** (early OOS PF 0.77) | `reports/improve/20260729-ae6-flush-fade.md` |
| AE6b | AE6 × bear/sideways gate | **Falsified** (sparse; deep-bear PF 0.13) | `…ae6b-regime-gate.md` |
| AE7 | funding ≤ −0.05% | **Untestable** (0 events, OKX/Bitget ~3m) | `…ae7-funding-event.md` |
| AE7b | train 10th-pct funding | **Falsified** | `…ae7b-funding-percentile.md` |
| AE8 | 1h disparity &lt; 97 | **Falsified** (early −12.65%, PF 0.51) | `…ae8-disparity-stretch.md` |
| AE9 | 4h EMA20 reclaim + ADX/DI | **Falsified** | `…ae9-trend-pullback.md` |
| AE10 | 4h MACD + ADX/DI | **Falsified** (WR 0%) | `…ae10-macd-trend.md` |
| AE11 | 1d BB upper breakout | **Falsified** (primary −24.9%) | `…ae11-daily-bb-breakout.md` |
| AE12 | lag-MDD + forward collect | **Done** (MDD material; collectors shipped) | `…ae12-lag-mdd.md` |
| AE12b H1 | funding ≤ **−0.0002** → next-day KRW-BTC | **RETAINED_for_research** | `…ae12b-event-study.md` |
| AE12b H2 | \|OB imbalance\| ≥ **0.4** → next 1h | **NOT_READY** (2 rows; need ≥336) | same |
| AE12c | H1 fee/slip ladder | **SURVIVES 20bps** (through 30; fails 50) | `…ae12c-fee-stress.md` |
| AE13 H_rich | Upbit premium ≥ train 90th → fade | **RETAINED_for_research** | `…ae13-upbit-premium.md` |
| AE13 H_cheap | premium ≤ train 10th → bounce | **Falsified** | same |
| AE13b | H_rich fade fee/slip ladder | **SURVIVES 20bps** (through 30; fails 50) | `…ae13b-fee-stress.md` |
| AE14 | paper-log H1+H_rich + Bitget forward | **PARTIAL** (H2 still pending) | `…ae14-paper-log-spec.md` |
| AE15 | Bitget mark−index basis rich-tail | **Registered** (not scored) | same spec §AE15 |

Cheatsheet: `reports/review-state/regime-engine.json` → `next[]`  
Per-id: `reports/review-state/alpha-ae*.json`

---

## 4. Research shelf (승격 아님)

### 4.1 Funding H1 (AE12b + AE12c)

- **Frozen cut:** `fundingRate <= -0.0002` (절대 재탐색 금지)
- **Source for hist study:** **HTX** `BTC-USDT` funding (OKX/Bitget 공개 이력 ~3개월 → 이벤트 0)
- **Holdout:** last 30% of events by time
- **Holdout (gross):** n=45, mean **+0.39%**, hit **64.4%** vs baseline mean **−0.06%**, hit **49.1%**
- **Fee stress:** primary **20 bps** RT 생존 (net mean +0.19%); 50 bps에서 실패
- **Scripts:** `scripts/ae12_event_study.py`, `scripts/ae12c_fee_stress.py`
- **Forward log (OKX):** `scripts/ae12_forward_collect.py` → `reports/ae12-collect/*.jsonl` (gitignore)

### 4.2 Upbit rich-premium fade (AE13)

- **Definition:** `premium = KRW-BTC / (USDT-BTC * KRW-USDT) - 1`
- **Frozen rich cut:** train 90th ≈ **`0.004563`** (재적합 금지; 새 AE id 없이는 컷 변경 금지)
- **Holdout rich events:** n=21, mean **−0.63%**, hit **33%** vs baseline mean **−0.14%**, hit **49%**
- **Cheap bounce:** falsified — 버려도 됨
- **Fee stress (AE13b):** primary **20 bps** RT 생존 (net fade mean +0.43% vs always-short +0.14%); through 30; fails 50
- **Script:** `scripts/ae13_upbit_premium_study.py`, `scripts/ae13b_fee_stress.py`
- KRW-USDT daily history ≈ 2024-06~ (overlap ~783d)

---

## 5. Anti-overfit 규칙 (필수)

1. **가설·임계값을 먼저 동결**한 뒤 한 번만 채점. 진 뒤 threshold sweep 금지.
2. **Time holdout** (보통 last 30% events 또는 train 70% / holdout 30%).
3. Early OOS / prior window에서 깨지면 **즉시 종료** (AE6–AE11 방식).
4. AE6–AE11 계열 **vanilla TA scrape 재시작 금지**.
5. Funding / premium **컷 재탐색 금지** (새 AE id + 사전 등록 없이).
6. Research retain ≠ promote. **Policy C / `STRATEGY_PATH` / LIVE 변경 금지** without:
   - 새 AE id
   - walk-forward + `scripts/strategy_audit.py` (G1–G8)
   - 사람 승인
7. Gemini-style “transition→sideways / ±3% SMA / switch market-sell” **거부 유지** (Policy C 재백테스트 없이).

---

## 6. VPS / 로컬 운영 할 일 (코드 외)

```cron
# 이미 있을 수 있음 — closed-bar switcher
20 15 * * * cd ~/auto-trade && python3 scripts/remote_regime_switch.py >> logs/regime-switch.cron.log 2>&1

# AE12 forward collect (H2용) — 아직 얇음 (각 2행)
*/30 * * * * cd ~/auto-trade && python3 scripts/ae12_forward_collect.py >> logs/ae12-collect.cron.log 2>&1

# Monthly LIVE review (Williams/Policy C ops — no auto-deploy)
0 16 1 * * cd ~/auto-trade && python3 scripts/monthly_live_review.py >> logs/monthly-review.cron.log 2>&1
```

- `remote_regime_switch.py` ops 가드본이 VPS에 복사됐는지 확인 (PR #6 계열).
- Collect JSONL은 gitignore — 로컬/VPS에만 쌓임.
- H2 ready 조건: `upbit-orderbook.jsonl` **≥ 336** rows 후  
  `python3 scripts/ae12_event_study.py` 재실행 (컷 변경 없이).

---

## 7. AE14 — 다음에 할 일 (우선순위)

### P0 — 데이터 게이트
1. OB collect 가동 확인 → rows ≥ 336이면 **H2만** 재채점 (`ae12_event_study.py`).
2. H2 실패/미준비여도 funding/premium 컷 건드리지 말 것.
3. 로컬(2026-07-29): `upbit-orderbook.jsonl` **없음** → H2 NOT_READY.

### P1 — Research shelf 심화 (승격 아님)
1. ~~AE13 **H_rich**에 AE12c식 fee-stress (20 bps primary)~~ — **DONE** AE13b SURVIVES_PRIMARY_FEE.
2. H1 + H_rich를 **전략 JSON이 아닌** 이벤트 규칙으로 paper 로그 설계만 (사람 승인 전 LIVE 연결 금지).
3. 수수료·슬리피지·갭 리스크 명시한 1페이지 스펙.

### P2 — 새 직교 아이디어 (선택)
- TA scrape / funding cut mining 아닌 것만.
- 예: 세션/캘린더, 실현변동성 사이즈 오버레이, 다른 거래소 basis (소스 명시 + 동결).
- 새 아이디어 = **AE15+** id, 가설·falsify 기준 문서화 후 실행.

### 하지 말 것
- AE6–AE11 재탕
- Policy C 파라미터/맵 “살짝” 수정
- Switch 시 자동 market-sell
- Threshold grid search after looking at returns

---

## 8. 주요 파일 인덱스

| Path | Role |
|------|------|
| `reports/review-state/regime-engine.json` | 엔진 치트시트 + `next[]` |
| `reports/improve/20260729-ae12*.md` | lag / event / fee |
| `reports/improve/20260729-ae13-upbit-premium.md` | premium study |
| `reports/improve/20260728-remaining-improvements.md` | 진행 보드 |
| `scripts/ae12_lag_mdd.py` | lag MDD |
| `scripts/ae12_forward_collect.py` | OKX funding + Upbit OB JSONL |
| `scripts/ae12_event_study.py` | H1 HTX + H2 OB |
| `scripts/ae12c_fee_stress.py` | H1 fee ladder |
| `scripts/ae13_upbit_premium_study.py` | premium H_rich / H_cheap |
| `scripts/ae13b_fee_stress.py` | H_rich fade fee ladder |
| `scripts/remote_regime_switch.py` | LIVE path swap + guards |
| `docs/regime-auto-switch-playbook.md` | ops + lag cadence |
| `.agents/skills/create-strategy/SKILL.md` | 전략 JSON 작성 |
| `.agents/skills/backtest/SKILL.md` | 백테스트·해석 |

---

## 9. 환경 노트 (클라우드에서 겪은 것)

- Binance futures 종종 **HTTP 451**; Bybit **403**. OKX / HTX / Upbit 사용 가능.
- H1 히스토리는 **HTX**로 확정. Forward collector는 OKX — 소스 섞어 한 테스트에 넣지 말 것 (새 AE id 필요).
- `uv` + `.agents/skills/*/scripts/upbit-strategy-toolkit.sh` 래퍼 사용.
- 미커밋 노이즈: `reports/alpha-ae6-*-043*.csv` 세그먼트 CSV — 커밋하지 말 것.

---

## 10. Local agent용 복붙 프롬프트

아래 블록을 로컬 Cursor 에이전트 첫 메시지로 그대로 붙여넣으면 됨.

````markdown
# Task: Continue Upbit auto-trade alpha research (AE14+)

You are continuing work from a cloud-agent handoff. Read and follow:

**Primary handoff:** `docs/handoff-alpha-local-agent.md`  
**State:** `reports/review-state/regime-engine.json` (`next[]`, especially AE14)  
**Branch:** `cursor/alpha-ae6-flush-fade-d7d9` (sync with origin first)

## Goal
Build **orthogonal alpha** without overfitting. Keep **Policy C / LIVE unchanged** unless a new AE id passes walk-forward + `scripts/strategy_audit.py` + explicit human approve.

## Hard rules
1. Do **not** restart AE6–AE11 TA scrapes.
2. Do **not** mine/retune frozen cuts:
   - funding H1: `fundingRate <= -0.0002`
   - premium rich: train 90th ≈ `0.004563` (from AE13; do not refit on full sample)
3. Freeze hypothesis + falsification criterion **before** scoring; time holdout; one shot.
4. Research retain ≠ promote. No Policy C map / STRATEGY_PATH / auto market-sell on regime switch.
5. Reject ad-hoc SMA ±3% buffers and transition→sideways without full Policy re-backtest.

## Research shelf (do not discard; do not blindly promote)
- Funding H1 (HTX hist): retained; survives 20–30bps RT fee stress (`reports/improve/20260729-ae12b-event-study.md`, `…ae12c-fee-stress.md`)
- Upbit rich-premium fade: retained; cheap bounce falsified (`…ae13-upbit-premium.md`)

## Do next (AE14 priority)
1. Check `reports/ae12-collect/upbit-orderbook.jsonl` row count. If ≥336, re-run `python3 scripts/ae12_event_study.py` for **H2 only** (same frozen `|imbalance|>=0.4`). Record verdict under new/updated improve report; no cut changes.
2. If H2 not ready: implement **AE13b** fee-stress on H_rich (mirror `scripts/ae12c_fee_stress.py`, primary 20bps). Or design paper-log spec for shelf ideas — still no LIVE wiring.
3. Only then consider AE15+ truly new orthogonal idea (not TA scrape / not cut mining). Document hypothesis + falsify criterion first.

## Ops reminder (separate from alpha)
VPS may still need updated `remote_regime_switch.py` (closed bar, dwell, cancel+position_skip) and optional `*/30` cron for `ae12_forward_collect.py`.

## Deliverables each iteration
- Report under `reports/improve/YYYYMMDD-aeNN-*.md` + JSON raw if study
- Update `reports/review-state/regime-engine.json` `next[]` and a small `alpha-aeNN-*.json`
- Commit on `cursor/alpha-ae6-flush-fade-d7d9` (or a new `cursor/...-d7d9` branch if splitting). Do not commit ae6 segment CSVs or ae12-collect JSONL.

Start by reading the handoff MD and confirming git branch / AE14 status, then execute the highest-priority ready step.
````

---

## 11. 한 줄 체크리스트 (로컬 착수 전)

- [ ] `git checkout cursor/alpha-ae6-flush-fade-d7d9 && git pull`
- [ ] `docs/handoff-alpha-local-agent.md` 읽기
- [ ] OB jsonl 행 수 확인 → H2 or AE13b 분기
- [ ] LIVE/Policy C 파일 경로 안 바꿈
- [ ] 결과 MD + review-state 갱신 후 커밋
