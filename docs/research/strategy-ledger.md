# 전략 원장 (Strategy Ledger) — 묘지 + 생존자

> 작성: edge-scout · 2026-10-08 · 보드 T-001  
> 근거는 기존 문서·리포트만 읽어 정리했다(백테스트 재실행 없음). 수치는 원문 그대로 옮겼고, 수수료는 포함, 슬리피지·호가·부분체결은 대부분 반영하지 않았다.  
> 판정 기준: **KILL** = 사전 기각 기준에 걸림 / **PARTIAL** = 형식상 생존 또는 일부 구간만 생존(승격 불가) / **SURVIVE** = OOS·수수료 스트레스 통과 / **LIVE** = 현재 실거래 / **미검증** = 코드·카드만 있고 판정 기록 없음.

## 지금 돌고 있는 것 (2026-10 기준)

| 슬롯 | 무엇 | 상태 | 근거 |
|---|---|---|---|
| w1 Upbit CORE | Policy C (bull·transition→`regime-bull-trend-4h-v2`, bear→`m5-v6`, sideways→`regime-sideways-mr-4h-v5`) | **LIVE** | `docs/regime-auto-switch-playbook.md`, `docs/dual-sleeve-allocation.md` |
| w5 Bitget scalp FT | `TrendShortV1` di_cloud ADX≥15 SL3/TP9, 5m, bear 전용 숏 | **LIVE** (고정 100 USDT, 8bps 스트레스 실패를 사람이 수용) | `config/scalp-live-map.json`, `freqtrade-research/user_data/config.bitget-scalp-trend-short-live.json` |
| w2 Bitget 봇 | SMA 크로스 (`bitget_btc_usdt_sma.json`) | **PAPER** | `VERSION.md`, `strategies/bitget_btc_usdt_sma.json` |

주의: Williams 1h sideways 카드가 2026-07-29 사람 승인으로 LIVE 승격된 기록이 있다(`reports/improve/20260729-williams-live-promote.md`, dwell<7이면 4h-v5로 대체). 현재 정본 맵 문서는 sideways=4h-v5라서, 실제 서버에서 어느 쪽이 붙어 있는지는 `regime-current.json`으로 확인해야 한다.

---

## 1. 원장 표

### 1-1. 레짐 스위치 / 정책 (Policy C 계열)

| 이름 | 데이터 우물 | 종목·TF | 판정 | 핵심 수치 | 근거 |
|---|---|---|---|---|---|
| Policy C (5y in-sample) | 레짐 스위치 | KRW-BTC 1d 레짐 + 4h/1h | **LIVE** | +425.9% / MDD −32.2% vs B&H +109% / −74% | `docs/research/fair-race-policyC-vs-rebalance.md` |
| Policy C OOS 2018-04→2021-07 | 레짐 스위치 | KRW-BTC | **SURVIVE** (MDD만) | +387.4% vs B&H +393.9%; MDD −36.7% vs −66.6%; 25 segs | `docs/research/policyC-oos-presample-2018-2021.md` |
| Policy C 수수료 2× | 레짐 스위치 | KRW-BTC | **SURVIVE** | OOS +387% → +320% | `docs/research/policyC-fee-stress-2x.md` |
| Policy C bull-v1 (EMA8/21) | 레짐 스위치 | KRW-BTC | 교체 | 5y chain +336% (v2는 +415%) | `reports/five-year/README.md` |
| Policy C → ETH 이식 | 레짐 스위치 | KRW-ETH | **PARTIAL** | IS +47.9%/−50.6% vs hold +7.4%/−77.4%; OOS +615% vs +404% | `docs/research/policyC-eth-transfer.md` |
| Policy C → QQQ 이식 | 레짐 스위치 | Bitget QQQUSDT 1h | KILL | −8.4% vs hold +13%, PF 0.38, n=26 (9개월) | `docs/research/policyC-qqq-bitget-transfer.md` |
| Famous mount (Faber SMA + Wilder RSI) | 레짐 스위치 | KRW-BTC 1d | KILL | IS +31.1%/−17%; OOS +6.1%/−16.8% (Policy C 대비 −380%p) | `docs/research/famous-vs-policyC-race.md` |
| R4 차입 레짐 | 레버리지·차입 | KRW-BTC | KILL | IS +269%/−45.6%; OOS +18%/−36.7% | `docs/research/borrow-r4-vs-policyC.md` |
| Policy 비교 sweep (v3/v6/v6b/v7 × sw3/4) | 레짐 스위치 | KRW-BTC | 참고 | chain +177~214% vs B&H +73% (구 레짐 v1) | `reports/sweeps/policy-compare-v7.json` |
| 스캘프 레짐 게이트 vs 무게이트 | 레짐 스위치 | Bitget BTC 5m | KILL | 게이트 ON PF 0.00/0.38 | `freqtrade-research/reports/20260729-regime-gate-vs-ungated.md` |
| Sideways MR ADX switch | 레짐 스위치 | BTC 1h | KILL | PF 0.46/0.57 | `freqtrade-research/reports/20260729-sideways-mr-adx-switch.md` |

### 1-2. 모멘텀·추세 (EMA/ADX/MACD/돌파)

| 이름 | 데이터 우물 | 종목·TF | 판정 | 핵심 수치 | 근거 |
|---|---|---|---|---|---|
| `regime-bull-trend-4h-v2` (EMA5/20, SL10/TP40) | 모멘텀·추세 | KRW-BTC 4h | **LIVE** (Policy C bull 슬리브) | 단독 always-on OOS +890%/−30% | `docs/research/mid-swing-4h-ema-adx-v1.md`, `reports/five-year/README.md` |
| `m5-v6` (1h EMA+ADX23+RSI55, SL3/TP4.5) | 모멘텀·추세 | KRW-BTC 1h | **LIVE** (bear 슬리브만) | 5y always-on −14.2% vs B&H +117.9%, PF 1.06; Y5 +14% | `reports/five-year/README.md`, `docs/KRW-BTC-strategy-pack-agent.md` |
| m5 계열 v2/v3/v4/v4b/v5/v6b/v6c/v7, gc-pdi-obv | 모멘텀·추세 | KRW-BTC 1h | KILL/HOLD | v7 감사 REJECT(n=7), v6b/c HOLD, v3 5y −58% | `reports/audit/20260728-summary.md`, `reports/five-year/README.md` |
| AE4 bull 대체군 7종 (MACD/DI/Ichi/SMA/SMA10-50/CCI/StochRSI/OBV) | 모멘텀·추세 | KRW-BTC 4h | KILL | 어느 것도 Policy C chain +425.85% 못 넘음 | `reports/improve/20260728-ae4-bull-family.md` |
| bull 4h entry v3/v4, exit v5–v8 (EMA-DI, EMA50 exit, sell-suppress) | 모멘텀·추세 | KRW-BTC 4h | KILL (미채택) | v2 대비 비교만, 맵 변경 없음 | `reports/bull-entry-v*-20260805/`, `reports/bull-exit-v*-20260805/` |
| bull-swing-4h-ema21-reclaim-v1 | 모멘텀·추세 | KRW-BTC 4h | KILL | Policy C bull 4h에 지배됨 | `docs/research/regime-daytrade-edge-pack-frozen.md` |
| mid-swing-4h-ema-adx-v1 | 모멘텀·추세 | KRW-BTC 4h | KILL | IS −21.6%; OOS −18.4% | `docs/research/mid-swing-4h-ema-adx-v1.md` |
| AE9 trend pullback | 모멘텀·추세 | KRW-BTC 4h | KILL | 초기 창 PF≪1 | `reports/improve/20260729-ae9-trend-pullback.md` |
| AE10 MACD trend | 모멘텀·추세 | KRW-BTC 4h | KILL | early OOS WR 0%, PF 0 | `reports/improve/20260729-ae10-macd-trend.md` |
| AE11 daily BB breakout | 모멘텀·추세 | KRW-BTC 1d | KILL | 최근 1년 WR 0% | `reports/improve/20260729-ae11-daily-bb-breakout.md` |
| daytrade bull pullback v1–v9 | 모멘텀·추세 | KRW-BTC 10m/15m | KILL | 종료·재개 금지 | `docs/research/regime-daytrade-edge-pack-frozen.md` |
| SMA 5/20 골든크로스 (+filtered v1–v3), sma_cross_btc | 모멘텀·추세 | KRW-BTC 1d | 미검증 (초기 봇, 교체됨) | 판정 문서 없음 | `strategies/sma-5-20-*.json`, `reports/review-state/` |
| Bitget SMA (`bitget_btc_usdt_sma`, w2) SMA5/20 교차 SL3/TP6 | 모멘텀·추세 | Binance BTCUSDT 무기한 1h 2019-09~2026-09 (Bitget 대용) | **KILL** (T-033, 현행 값 freeze) | n=2,044(OOS 954, 연 293회); OOS x2 PF 0.66 평균 −0.27%, 기본 수수료만도 PF 0.92; 무작위 56백분위; 8개 연도 전부 PF<1; 노출 Sharpe −3.66 vs B&H 0.75; ETH OOS −0.29% | `docs/research/results/w2-bitget-sma5-20-1h.md` |
| bear short scalp v1–v12 (RSI×EMA, HTF fade, BB breakdown, failed reclaim, −DI, Donchian, 4h gate, EMA50, Stoch fade) | 모멘텀·추세 | Bitget BTC 5m–1h | KILL | 전부 3창 중 ≥2 실패 (PF 0.10–0.98) | `reports/improve/20260729-bear-short-scalp.md` |
| BearShortDivAtrV13 | 모멘텀·추세 | Bitget BTC | KILL | PF 0.04 / 0.93 | `reports/improve/20260730-bear-short-div-atr-v13.md` |
| TrendShortV1 di_cloud ADX15 5m SL3/TP9 | 모멘텀·추세 | Bitget BTCUSDT 5m | **LIVE** (PARTIAL) | h1 PF 1.44 n=27, h2 PF 1.20 n=33; 10–12bps에서 실패 | `reports/bitget-btc-short-swing-hit/README.md`, `reports/bitget-btc-short-swing-deep-20260805/README.md` |
| TrendShortV1Lev3 (같은 수익비 출구) | 레버리지·차입 | Bitget BTC 5m | KILL | PF 0.96 / 0.84, 거래 200+ | `freqtrade-research/reports/trend-short-lev3-20260806/NOTES.md` |
| TrendShortV1Lev3Px (가격 일치 출구) | 레버리지·차입 | Bitget BTC 5m | PARTIAL | PF 1.45 / 1.18, DD 5.5/7.3% | 같은 파일 |
| AltBearShortDonchian/Stoch, Visual5mBearShort v1–v2 | 모멘텀·추세 | 알트/BTC 5m | 미검증 | 판정 문서 없음 | `freqtrade-research/user_data/strategies/` |
| Famous Faber 10mo SMA | 모멘텀·추세 | KRW-BTC 1d | KILL (Famous race 참조) | — | `docs/regime-famous-mount.md` |

### 1-3. 평균회귀 / 오실레이터 페이드 / 다이버전스

| 이름 | 데이터 우물 | 종목·TF | 판정 | 핵심 수치 | 근거 |
|---|---|---|---|---|---|
| `regime-sideways-mr-4h-v5` | 평균회귀 | KRW-BTC 4h | **LIVE** (Policy C sideways 슬리브) | 단독 판정 없음, 맵 안에서만 | `docs/research/fair-race-policyC-vs-rebalance.md` |
| sideways 4h v2/v3/v4/v4b/v4c, 1d v1/v2 | 평균회귀 | KRW-BTC 4h/1d | 교체 | v4→v5로 교체 | `strategies/regime-sideways-mr-*.json` |
| `regime-sideways-mr-1h-williams-v1` | 평균회귀 | KRW-BTC 1h | **PARTIAL** (LIVE 승격 기록) | SW 3창 PF 1.51–1.85, +0.5~0.6%; 6창 중 clear pass 3; always-on −20% | `reports/improve/20260729-sideways-mr-research-loop.md`, `reports/improve/20260729-williams-multi-window.md` |
| Williams dwell≥14 가드 | 평균회귀 | KRW-BTC 1h | PARTIAL | stub 실패 제거, 승격 근거 아님 | `reports/improve/20260729-williams-dwell14-guard.md` |
| sideways 1h: adx-switch, bb-reclaim, stochrsi v2–v4, cci-fade, early-strict v2 | 평균회귀 | KRW-BTC 1h | KILL | SW PF 0–0.74 | `reports/improve/20260729-sideways-mr-research-loop.md` |
| Bitget Stoch/Williams MR (FT) | 평균회귀 | Bitget BTC 1h | KILL | Williams PF 1.11/1.13/0.46; Stoch PF 0.06–1.11 | `freqtrade-research/reports/bt-williams-*.txt`, `bt-stoch*-*.txt` |
| AE6 MFI+WR flush fade / AE6b 레짐 게이트 | 평균회귀 | KRW-BTC 4h | KILL | AE6b deep-bear PF 0.13 | `reports/improve/20260729-ae6-flush-fade.md`, `…ae6b-regime-gate.md` |
| AE8 disparity stretch | 평균회귀 | KRW-BTC 1h | KILL | early OOS 붕괴 | `reports/improve/20260729-ae8-disparity-stretch.md` |
| Upbit scalp 5m RSI-BB v1–v4, 1m RSI-Ichi v1–v3, 5m RSI-Ichi v4 | 평균회귀 | KRW-BTC 1m/5m | KILL | — | `strategies/krw-btc-*-scalp-*.json` |
| RsiBbScalpLongShortV4 (FT) | 평균회귀 | Bitget BTC 5m | KILL | 3창 모두 PF<1 | `freqtrade-research/reports/20260729-rsi-bb-longshort-v4.md` |
| RSI-Ichi 5m long | 평균회귀 | Bitget BTC 5m | PARTIAL (수수료 전) | OOS 반쪽 PF 1.46/1.53 (fee 전), n~180 | `strategies/bitget-btc-5m-rsi-ichi-long-short-v1.notes.md` |
| maker-fill-rsi-ichi-5m-long (RSI-Ichi 5m long 원본 값, 지정가 관통 체결 N=1 vs 테이커) | 체결 방식 × 평균회귀 | Binance BTC/ETH 무기한 5m, OOS 2020-01~2025-08 ∪ 2026-08~10 | **KILL** (T-035) | 신호 1,605, 진입 체결률 98.0%, 청산 지정가 96.0%; B x2 PF 0.265(A 0.061), 수수료 0도 A 0.886 / B 0.609; 무작위 0백분위; 절반 0.27/0.26; ETH 0.32; 역선택: 미체결 반사실 +0.19% vs 체결 −0.017% (t −6.05); IS 재현 수수료 0 PF 1.145(업비트 원본 1.46~1.53) | `docs/research/results/maker-fill-rsi-ichi-5m-long.md` |
| RSI-Ichi short v1–v4, RSI-BB short v5, 5m/1m 스캘프 그리드 | 평균회귀 | Bitget BTC 1m/5m | KILL | 수수료 후 최고 minPF 0.86–0.93; PF≥1.10@n150 0건 | `reports/scalp-pf-threshold-20260805/NOTES.md` |
| daytrade side BB fade v1–v8; `SidewaysEdge15mBbFadeV5` | 평균회귀 | KRW-BTC/Bitget 10m/15m | KILL (v5는 SCALP LIVE 후 정지) | 07-30 수수료·슬리피지로 정지 | `config/scalp-live-map.json` |
| SidewaysScalp15mBbV1 | 평균회귀 | Bitget BTC 15m | KILL | 샘플 창 기각 | `reports/improve/20260729-dual-sleeve-allocation.md` |
| daytrade BB-RSI div v1–v70 (~90장) | 평균회귀 | KRW-BTC 5m–1h | KILL | 0거래 / FEE_BLEED / SPARSE | `reports/automation/daytrade-strategy-oos-report-20260730.md` |
| daytrade-edge 15m-div v1/v3, 10m-div v1/adx/atr | 평균회귀 | KRW-BTC 10m/15m | PARTIAL | OOS 3창 net+ 1~2/3, 창당 1–8거래; 10m-atr worst −0.05% | `reports/automation/oos-validate-20260730.md` |
| `DaytradeEdge10mDivAtrV1` (Bitget) | 평균회귀 | Bitget BTC 10m | KILL (SCALP LIVE 후 정지) | 07-30 정지 | `config/scalp-live-map.json`, `docs/research/regime-daytrade-edge-pack-frozen.md` |
| Famous Wilder RSI MR | 평균회귀 | KRW-BTC 1d | KILL (Famous race) | — | `docs/regime-famous-mount.md` |

### 1-4. OHLCV 캔들패턴 / 유동성 스윕

| 이름 | 데이터 우물 | 종목·TF | 판정 | 핵심 수치 | 근거 |
|---|---|---|---|---|---|
| 나씨 3봉 페이드 | 캔들패턴 | BTC 15m | KILL | 3/3 음수 | `freqtrade-research/reports/20260729-nassi-3bar-fade-v1.md` |
| 나씨 3봉 페이드 + DCA | 캔들패턴 | BTC 15m | KILL | 2/3, 추세 런에 −20% 바닥 | `…/20260729-nassi-3bar-fade-dca-v1.md` |
| 나씨 3틱 롱 DCA V1 | 캔들패턴 | BTC | PARTIAL (형식) | +0.16 / −2.41 / +0.08% | `…/20260729-nassi-3tick-long-dca-v1.md`, `…abc-summary.md` |
| 나씨 3틱 A1 (상태머신) | 캔들패턴 | BTC | PARTIAL (형식) | 1/3 실패, 6월 −20% 백 스탑 | `…/20260729-nassi-3tick-a1.md` |
| 나씨 3틱 B1 (레짐) | 캔들패턴 | BTC | PARTIAL (형식) | 0/3 실패, net +0.1% 급 | `…/20260729-nassi-3tick-b1.md` |
| 나씨 3틱 C1 (찐바닥) | 캔들패턴 | BTC | PARTIAL (형식) | 0/3 실패, B와 비슷 | `…/20260729-nassi-3tick-c1.md` |
| 나씨 3틱 B1-TP05 | 캔들패턴 | BTC | PARTIAL (형식) | 스트레스 월 B보다 나쁨 | `…/20260729-nassi-3tick-b-tp05.md` |
| 나씨 3틱 B1 Lev5 TP03/TP05 | 레버리지·차입 | BTC | KILL | 6월 −3.99% / −7.21% | `…/20260729-nassi-3tick-b-lev5-tp.md` |
| Hammer reclaim long | 캔들패턴 | BTC 15m | KILL | 3/3 | `…/20260729-hammer-reclaim-long-v1.md` |
| BTC dump sweep fade R3 (always-on) | 캔들패턴(스윕) | Binance BTC 15m 2021–26 | KILL | n=1353, PF 0.76, −78.5% | `docs/research/btc-dump-sweep-fade-r3-v1.md` |

### 1-5. 박스·채널 (빗각·S/R)

| 이름 | 데이터 우물 | 종목·TF | 판정 | 핵심 수치 | 근거 |
|---|---|---|---|---|---|
| BTC day box fade V1 / V2 | 박스·채널 | BTC 15m | KILL | 3/3; 스탑 지배 | `freqtrade-research/reports/20260729-btc-day-box-fade-v1.md`, `…-v2.md` |
| BTC swing box fade V1 | 박스·채널 | BTC | KILL | 3/3 | `…/20260729-btc-swing-box-fade-v1.md` |
| 빗각 LR scalp v1 / retest v2 / 15m v3 | 박스·채널 | ETH 5m/15m | KILL | PF 0.18–0.76 | `reports/improve/20260729-diagonal-빗각-scalp.md` |
| Diagonal volume-pivot day V1 | 박스·채널 | BTC 15m | KILL | PF 1.06/0.79/0.60 | `…/20260729-diagonal-volume-pivot-day-v1.md` |
| Diagonal volume-pivot day V2 (Mode B) | 박스·채널 | BTC 15m | PARTIAL (승격 안 함) | PF 0.66/1.10/1.16, n 작음 | `…/20260729-diagonal-volume-pivot-day-v2.md` |
| V1-gate / Human-Soft / Multi-TF / US-RTH MTF | 박스·채널 | BTC 4h→15m | KILL | 전부 ≥2/3 PF<1 | `…/20260729-diagonal-*.md`, `docs/inbum-diagonal-channel-playbook.md` |
| QQQ US-RTH MTF / QQQ Mode B frozen | 박스·채널 | Bitget QQQ 4h→15m | KILL | PF 0.40/0.40/0; Mode B +0.99/−0.91/−2.64% | `…/20260729-diagonal-qqq-*.md` |
| 수동 채널 표본 batch1, ICT 오버레이 | 박스·채널 | BTC | 미검증 (정성 표본) | — | `docs/research/channel-manual-sample-batch1.md`, `channel-clearest3-ict-overlay.md` |

### 1-6. 캘린더 이벤트

| 이름 | 데이터 우물 | 종목·TF | 판정 | 핵심 수치 | 근거 |
|---|---|---|---|---|---|
| cal-event vol reclaim R10 (FOMC/CPI/NFP) | 캘린더 이벤트 | Binance BTC 15m 2021–26 | KILL | n=113, PF 0.51, TP 4/113 | `docs/research/cal-event-vol-reclaim-r10-v1.md` |
| cal-event sweep fade R3 | 캘린더 이벤트 | Binance BTC 15m | PARTIAL | train PF 0.78; holdout PF 1.12 n=18 | `docs/research/cal-event-sweep-fade-r3-v1.md` |
| weekend-gap-fade-btc-eth (주말 ±2% → 월요일 1일 되돌림) | 세션·주말 | Binance BTC/ETH 무기한 1d 2018–26 | KILL | n=421; OOS n=120 x2 평균 −0.29% PF 0.81, 무작위 57백분위, ETF 이후 −0.22%, BTC·ETH 둘 다 음수; 업비트 롱만 OOS PF 1.08 | `docs/research/results/weekend-gap-fade-btc-eth.md` |

### 1-7. 리밸런스·배분

| 이름 | 데이터 우물 | 종목·TF | 판정 | 핵심 수치 | 근거 |
|---|---|---|---|---|---|
| BTC:현금 50:50 ±12%p cd30 | 리밸런스 | KRW-BTC 1d 5y | KILL (엣지로서) / 운영용 LIVE | +77.4% / MDD −45.3% | `docs/research/fair-race-policyC-vs-rebalance.md` |
| 80:20 ±10%p cd14, 70:30, aggressive, 8020 band grid, 10y weights | 리밸런스 | KRW-BTC | KILL (엣지로서) | 80:20 +105% / −65.8% | 같은 파일, `reports/bt-*-rebalance-5y*.json`, `bt-weights-10y*.json` |
| Major-bull 재진입 + Bitget lev 헤지 | 레버리지·차입 | BTC | 미검증 (설계만) | — | `docs/bull-reentry-and-lev-hedge.md` |

### 1-8. 비-OHLCV: 펀딩·호가·김프

| 이름 | 데이터 우물 | 종목·TF | 판정 | 핵심 수치 | 근거 |
|---|---|---|---|---|---|
| AE7 펀딩 ≤ −0.05% | 펀딩 | OKX/Bitget → KRW-BTC 1d | 미검증 (이벤트 0건) | — | `reports/improve/20260729-ae7-funding-event.md` |
| AE7b 펀딩 하위 10% (train 분위수) | 펀딩 | OKX/Bitget → KRW-BTC 1d | KILL | holdout n=8, −0.19% vs 기준 −0.13% | `reports/improve/20260729-ae7b-funding-percentile.md` |
| AE12 H1 펀딩 ≤ −0.02% (HTX 이력) | 펀딩 | HTX → KRW-BTC 1d | **PARTIAL** | holdout n=45, +0.39% vs −0.06%, hit 64%; 30bps까지 생존, 50bps 실패 | `reports/improve/20260729-ae12b-event-study.md`, `…ae12c-fee-stress.md` |
| AE12 H2 호가 불균형 ≥0.4 | 호가창 | Upbit OB → 1h | 미검증 (수집 부족) | ≥336행 필요 | `reports/improve/20260729-ae12b-event-study.md` |
| AE13 H_rich 김프 ≥ 90분위 → 다음날 약세 | 김프·프리미엄 | Upbit KRW-BTC 1d | **PARTIAL** | holdout n=21, 페이드 +0.63% vs 기준 +0.14%; 30bps 생존 | `reports/improve/20260729-ae13-upbit-premium.md`, `…ae13b-fee-stress.md` |
| AE13 H_cheap 역김프 → 반등 | 김프·프리미엄 | Upbit KRW-BTC 1d | KILL | holdout 평균·적중 모두 기준 이하 | 같은 파일 |
| kimchi-rich 매수 스킵 오버레이 | 김프·프리미엄 | Upbit 라우팅 | 미검증 (AE14 페이퍼 스펙만) | — | `strategies/kimchi-rich-preposition-skip-v1.notes.md`, `reports/improve/20260729-ae14-paper-log-spec.md` |
| oi-flush-rebound (ΔOI 하위 5%+하락일 → 2일 롱) | OI·청산 | BTC/ETH/SOL 1d 2021-12~2026-09 | **KILL** (업비트 현물 KILL, 무기한은 레드팀 VETO: 시드 20개 중앙 92.9·날짜 묶음 85.6~89.6백분위, 거래소 두 번 시도, 2026 PF 0.34) | n=106(OOS 55, 연 16.9회); 업비트 OOS x2 +0.31% PF 1.30 무작위 79백분위; 무기한 +0.77% PF 1.75 무작위 95.3; 가격만 대비 OI 우위 통과; OOS 뒤 절반 PF 0.65/1.01, SOL 의존 | `docs/research/results/oi-flush-rebound.md` |
| upbit-caution-perp-short (업비트 유의종목 최초 지정 → 다음 UTC 시가 Binance 무기한 1배 14일 숏, 펀딩 포함) | 한국어 공지 이벤트 | Binance USDT-M 무기한 1d, 공지 2022-05~2026-09 | **KILL** (T-036 카드 → T-037 데이터 → 리서치, 사전 기준 8개 중 5개 실패) | n=32(train 4 / OOS 28, 2026에 21); OOS x2(왕복 0.8%)+펀딩 평균 −2.95%, 중앙 −0.11%, PF 0.72, 승률 50%; 날짜 묶음 달력 이동 17.3백분위(99 필요), 독립 무작위 28.3; BTC 숏 대비 −0.75%p, 알트 바스켓 숏 대비 −1.36%p; 펀딩 평균 −4.2%/건; 2026 PF 0.45 vs 2026 이전 OOS 7건 PF 8.2; −40% 초과 손실 2건(TAIKO 청산, DRIFT −75%) | `docs/research/results/upbit-caution-perp-short.md` |
| xs-funding-crowding-weekly (알트 30개 중 직전 7일 펀딩 상위 5 숏·하위 5 롱, 주간, 시장 중립) | 펀딩 × 크로스섹션 | Binance USDT-M 무기한 전체(상폐 포함) 1d, 2020-08-10~2026-09-28 | **KILL** (T-028 카드 → T-038 데이터 → T-039 리서치, 사전 기준 7개 중 3개 실패) | 321주(train 151 / OOS 170); OOS x2+펀딩 주 +0.005%, PF 1.002, 승률 48.2%, Sharpe 0.00 vs BTC B&H 0.94; 무작위(날짜 묶음) 81.7백분위(95·99 실패); 역모멘텀 −1.72%/주보다는 우위; train PF 1.65 → OOS 앞 절반 2.13 → 뒤 절반 0.67, 2025 PF 0.53; OOS 롱 다리 가격 −2.85%/주 vs 펀딩 +2.59%(캐리를 가격이 되가져감); 상위 3주 합 +71% vs OOS 합 +0.78%; 1배 숏 청산 OOS 24건(2025~ 23) | `docs/research/results/xs-funding-crowding-weekly.md` |

---

## 2. 요약

### 우물별 시도 수 vs 생존 수 (카드 단위, 대략)

| 데이터 우물 | 시도 | SURVIVE/LIVE | PARTIAL | 비고 |
|---|--:|--:|--:|---|
| 레짐 스위치 | ~10 | 1 (Policy C) | 1 (ETH 이식) | 생존은 사실상 "맵 하나" |
| 모멘텀·추세 | ~60 | 2 슬리브 (bull-v2, m5-v6 bear) + 1 LIVE (TrendShortV1) | TrendShortV1 자체가 PARTIAL | 단독 always-on으로는 모두 B&H 열세 |
| 평균회귀·오실레이터·다이버전스 | ~45 (+div 단타 ~90) | 1 슬리브 (sideways-4h-v5) | 3 (Williams 1h, 10m-div 계열, RSI-Ichi long fee 전) | 단타 SCALP LIVE 2장은 수수료로 정지 |
| OHLCV 캔들패턴·스윕 | 10 | 0 | 5 (형식만, net≈0) | 나씨 3틱은 경제적으로 무의미 |
| 박스·채널 (빗각·S/R) | ~14 | 0 | 1 (V2, 승격 안 함) | |
| 캘린더 이벤트 | 2 | 0 | 1 (R3, holdout n=18) | |
| 레버리지·차입 | ~6 | 0 | 1 (Lev3Px = 같은 엣지 확대) | 레버리지는 엣지가 아님 |
| 리밸런스·배분 | ~6 | 0 (운영 LIVE, 엣지 아님) | 0 | Policy C에 수익·MDD 모두 열세 |
| 펀딩 | 4 | 0 | 1 (AE12 H1) | 출처(HTX vs OKX/Bitget)에 따라 결과 반대. 알트 크로스섹션 펀딩 롱숏(T-039) KILL: 캐리를 가격이 되가져감 |
| 호가창 | 1 | 0 | 0 | 데이터 미수집 |
| 김프·프리미엄 | 3 | 0 | 1 (AE13 H_rich) | n=21 |

### 이미 판 우물 (재제안 금지)

1. **BTC OHLCV 캔들패턴 단타**: 나씨 3봉/3틱(DCA·레버리지 포함), 해머 reclaim, always-on dump sweep fade.
2. **박스·채널·빗각**: 일·스윙 박스 페이드, LR±2σ 레일, volume-pivot 채널 Mode A/B, 세션(US-RTH)·MTF 필터, QQQ 이식.
3. **BTC 1m/5m 스캘프 그리드** (RSI/BB/Ichimoku 페이드, 롱·숏 모두): 수수료 후 PF≥1.10@n150 0건.
4. **Bitget BTC 숏 단타 구조 v1–v13** (EMA/RSI/BB/Donchian/−DI/Stoch/Div ATR), 롱→숏 미러.
5. **bull 슬리브 대체** (MACD/DI/Ichi/SMA/CCI/StochRSI/OBV, entry v3–v4, exit v5–v8, EMA21 reclaim, mid-swing 4h, bull pullback 단타 v1–v9).
6. **sideways 1h 오실레이터 MR 변형** (StochRSI/BB reclaim/CCI/ADX switch).
7. **BB-RSI 다이버전스 단타 v1–v70**.
8. **Policy C 맵의 타 자산 이식** (QQQ 기각; ETH만 부분 생존) 및 Famous/차입/리밸런스 대체 경주.
9. **캘린더 매크로 이벤트 15m 재진입** (R10), 이벤트 스윕 페이드 R3의 손절·익절 쇼핑.

아직 덜 판 우물: 펀딩(출처 정합 필요), 호가 불균형(데이터 미수집), 김프(소표본), 크로스섹션 알트, OI·청산, 상장/공지, 거래소 간 지연, 변동성 프리미엄.

### 생존·부분 생존 자산 (정직한 단서 포함)

- **Policy C (LIVE, w1 Upbit)** — OOS 2018–21 수익 +387% vs B&H +394%(동률), MDD −37% vs −67%(절반), 수수료 2×에도 +320%. 단서: (a) 맵·bull-v2 파라미터는 2021–26 구간에서 골라졌고 5y +426%는 in-sample, (b) 수익 엣지는 OOS에서 재현되지 않았고 **MDD 엣지만** 재현, (c) 세그먼트 체인 시뮬(전환 마찰·슬리피지 미반영), (d) 레드팀 반증 전(T-003).
- **TrendShortV1 (LIVE, w5 Bitget)** — 5m di_cloud 숏, 두 반기 PF 1.44/1.20, n=27/33. 단서: 거래 수 적음, 8–10bps 스트레스 실패, 이웃 파라미터 4/7만 통과, 샘플 1년이 대체로 약세장.
- **Policy C → ETH** — 두 구간 모두 hold 대비 수익·MDD 우위. 단서: 이식만 확인, LIVE 아님, MDD −50% 수준으로 여전히 깊음.
- **AE12 H1 펀딩 음수 → 다음날 KRW-BTC** — holdout +0.39%/일, 30bps까지 생존. 단서: HTX 이력 기반, OKX/Bitget 상대 분위수 버전(AE7b)은 기각 → 출처 의존성 의심, 비중첩 n=45.
- **AE13 H_rich 김프 페이드** — holdout n=21, 30bps 생존. 단서: 표본 매우 작음, Upbit 현물은 숏 불가라 "매수 스킵" 오버레이로만 쓸 수 있음(페이퍼 미실행).
- **Williams 1h sideways** — sideways 창에서 PF 1.5–1.9지만 6창 중 3창만 확실 통과, 대부분 B&H에 뒤짐. LIVE 승격 기록 있음(소액, 페이퍼 생략).
- **cal-event sweep fade R3**, **daytrade-edge 10m-div-atr**, **Diagonal V2**, **나씨 3틱 B/C** — 형식 생존이지만 n·net이 노이즈 수준. 승격 근거 없음.

---

## 3. 교훈 (왜 죽었나)

- **수수료가 단타를 죽였다.** 1m–15m BTC 스캘프의 기대 이동폭(0.3–0.8%)에서 왕복 12bps가 15–40%를 먹는다. fee=0 PF 1.13 → 수수료 후 0.86–0.93. SCALP LIVE 2장(Div ATR, BB fade v5)도 수수료·슬리피지로 정지.
- **같은 우물을 변형만 바꿔 계속 팠다.** 다이버전스 단타 ~90장, 숏 단타 13판, 빗각 11판, 나씨 9판 — 모두 BTC OHLCV에서 파생된 같은 정보. 변형 수가 늘수록 "한 창만 좋은" 생존자가 우연히 나온다(v6/v9/v10 단일 창 승리 재현 실패).
- **always-on은 B&H를 못 이긴다; 살아남은 건 레짐 맥락 안에서만.** m5-v6 5y −14% vs B&H +118%, Williams always-on −20%. 슬리브는 레짐 맵 안에서만 의미가 있고, 그 맵의 엣지도 OOS에선 수익이 아니라 MDD뿐이었다.
- **표본이 작으면 생존이 아니다.** 창당 1–8거래, holdout n=18/21, "형식 생존"이 net +0.1% — PF 1.x는 노이즈. 비대칭 R:R(1:3, 1:10)은 적중률 15–27%로 무너졌다.
- **필터·레버리지 추가는 엣지를 만들지 않는다.** ADX/RSI 필터는 승자를 잘랐고(mid-swing), 레짐 게이트는 거래만 없앴고, 레버리지는 같은 출구를 좁혀 과매매로 PF<1을 만들었다(Lev3).
- **비-OHLCV 우물은 거의 안 팠고, 판 곳에서만 부분 생존이 나왔다.** 펀딩·김프 각 1건 PARTIAL. 다음 사이클은 여기서 시작하되 출처 정합·표본 확대가 먼저다.
