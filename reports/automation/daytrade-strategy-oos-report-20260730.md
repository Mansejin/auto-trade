# Daytrade 전략 보고서 + OOS 검증 (2026-07-30)

## 1. 인벤토리

| 항목 | 값 |
|------|-----|
| 카드 시도 | ~90 (`daytrade-bb-rsi-div-v1…v70` + edge 계열) |
| A–D PASS (연구 freeze) | 13+ (ledger `near_misses` / PROMOTED) |
| 봇 배포 | 0 (develop-only / SSH 금지) |
| 첫 승격 | `daytrade-edge-15m-div-v1` |
| 현재 최강 프로모 클러스터 | **10m classic+hidden OR** (여러 카드 3/3) |

### 페이즈

1. **v1–34** — 과엄격 / 0거래  
2. **v35** — 5m hidden bull near-miss (A 2/3)  
3. **v36–70** — 5m leave-OS/reclaim → FEE_BLEED · 고갈  
4. **15m-div-v1…** — 첫 A–D PASS 후 sibling (v2/v3/ATR/ADX/hold)  
5. **10m-div-*** — 프로모 창 3/3 다수 (densest)  
6. **30m / 1h / short-proxy** — SPARSE / WORST / A_FAIL

### 프로모 하이라이트 (May–Jul 프로모 창)

| Slug | 구조 | A | worst |
|------|------|---|-------|
| `daytrade-edge-15m-div-v1` | 15m hidden → upper | 2/3 | −0.21% |
| `daytrade-edge-15m-div-v3` | 15m ADX+OR → upper | 2/3 | −0.04% |
| `daytrade-edge-10m-div-v1` | 10m OR → upper | **3/3** | +0.05% |
| `daytrade-edge-10m-div-adx-v1` | 10m ADX+OR | **3/3** | +0.29% |
| `daytrade-edge-10m-div-atr-v1` | 10m ATR+OR | **3/3** | +0.05% |

## 2. OOS 검증 (다른 레인지)

프로모 창(May–Jul)과 **겹치지 않는** ~30d × 3:

| Window | Period |
|--------|--------|
| o1_feb | 2026-02-01 ~ 2026-03-02 |
| o2_mar | 2026-03-03 ~ 2026-04-01 |
| o3_apr | 2026-04-01 ~ 2026-04-30 |

대상 5카드: `15m-div-v1`, `15m-div-v3`, `10m-div-v1`, `10m-div-adx-v1`, `10m-div-atr-v1`.

상세 표: [`oos-validate-20260730.md`](oos-validate-20260730.md) · raw [`oos-validate-20260730.json`](oos-validate-20260730.json)

### OOS 요약

| Slug | net+ 창 | worst | 메모 |
|------|---------|-------|------|
| 15m-div-v1 | 2/3 | **−1.79%** | Mar PF 0.00 |
| 15m-div-v3 | **1/3** | −1.79% | 프로모 대비 약화 |
| 10m-div-v1 | 2/3 | −0.92% | Feb/Apr + |
| 10m-adx-v1 | 2/3 | −0.87% | Feb − |
| **10m-atr-v1** | 2/3 | **−0.05%** | OOS worst 최소 |

## 3. 사실 정리

- 프로모 통과 ≠ OOS 통과. 15m-v3는 OOS에서 1/3.  
- 10m-atr-v1이 OOS worst(−0.05%) 기준으로 가장 덜 깨짐.  
- 전 카드 거래 수 sparse (창당 1–8).  
- Feb 창 bench ≈ −18%에서 일부 long MR이 소폭 + (벤치 대비).  
- 수수료 on. 슬리피지·호가·부분체결 미반영.

재실행: `py -3 scripts/oos_validate_daytrade.py`
