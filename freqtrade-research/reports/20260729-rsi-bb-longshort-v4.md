# Freqtrade Bitget BTCUSDT-M — RSI-BB long/short v4

Date: 2026-07-29  
Pair: `BTC/USDT:USDT` futures isolated  
Fee: 0.06% taker  
Rules: long RSI<25+BB lower+ADX<30; short RSI>75+BB upper+ADX<30; ROI 0.8% / SL 0.3%

## Results (3 OOS windows)

| Window | Trades | Profit % | PF | Market | Long/Short n | Long PnL % | Short PnL % | ROI/SL exits | DD |
|---|---|---|---|---|---|---|---|---|---|
| 05-15~05-29 | 19 | -0.68% | 0.87 | -9.21% | 8/11 | -0.94% | **+0.26%** | 6/13 | 1.69% |
| 06-15~06-29 | 24 | -5.03% | 0.39 | -9.53% | 12/12 | -2.49% | -2.54% | 4/20 | 6.85% |
| 07-15~07-29 | 21 | -1.90% | 0.69 | -1.47% | 11/10 | -0.19% | -1.71% | 5/15 | 4.46% |

Notes:
- True long+short on Bitget futures (unlike Upbit toolkit proxy).
- Funding-rate history incomplete before ~2026-06-26 (freqtrade warning) — early windows slight funding bias possible.
- All 3 windows PF < 1.0 → unfiltered dual-direction scalp **not retained**.
- May: short side alone was slightly positive while long dragged — supports regime-bias hypothesis (bear → short-only).

## Files
- Strategy: `user_data/strategies/RsiBbScalpLongShortV4.py`
- Config: `user_data/config.bitget-futures-research.json`
- Raw logs: `reports/bt-*.txt`
