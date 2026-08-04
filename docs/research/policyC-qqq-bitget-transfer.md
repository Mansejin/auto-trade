# Policy C → Bitget QQQUSDT transfer (research)

> Not investment advice. Research only — **do not** mount to LIVE / Upbit Policy C.

| | |
|--|--|
| Pair | `QQQ/USDT:USDT` (Bitget USDT-M) |
| Strategy | `PolicyCQqqFuturesV1` |
| Config | `freqtrade-research/user_data/config.bitget-policyC-qqq.json` |
| Fee | 0.06% taker |
| Artifact | `freqtrade-research/user_data/backtest_results/backtest-result-2026-07-31_13-15-10.zip` |

## Map (frozen)

| Regime | Sleeve |
|--------|--------|
| bull / transition | long EMA5/20 4h (bull-v2) SL10/TP40 |
| bear | short invert m5-v6 1h SL3/TP4.5 |
| sideways | WilliamsR MR long+short 1h SL2/TP3 |

Classifier = regime engine v2 on **1h→1D resampled** QQQ (native Bitget 1d ≈93 bars &lt; SMA200).

## Data ceiling

- Bitget QQQ 1h from ~2025-10-28 (~275 calendar days).
- Effective BT after SMA200 warmup: **2025-11-07 → 2026-07-31** (~9 months).
- Underpowered vs BTC Policy C 5y sample.

## Result (full available window)

| Metric | Policy C–QQQ | QQQ market change |
|--------|-------------:|------------------:|
| Return | **−8.37%** | **+13.00%** |
| MDD (account) | −11.78% | (rising tape; hold MDD not separately modeled) |
| Trades | 26 | — |
| Win rate | 26.9% | — |
| Profit factor | 0.38 | — |
| Long / Short | 17 / 9 | — |

### By enter_tag (profit_ratio sum)

| Tag | n | note |
|-----|--:|------|
| `bull_ema_4h` | 7 | negative |
| `side_wr_long` | 10 | negative |
| `side_wr_short` | 9 | negative |
| `bear_m5v6_inv` | **0** | no bear-sleeve trades after warmup |

## Falsification

**Reject transfer** (do not promote):

1. Return (−8.4%) **below** QQQ hold (+13%).
2. Trades 26 ≈ noise floor; bear short sleeve sample = 0.
3. No evidence the Policy C map ports to Bitget QQQ with shorts in this history.

## Follow-ups (only if human wants)

- Longer QQQ history from another venue for regime/price (still research).
- Do **not** retune ADX/RSI/SL after this result.
