# Weekly CORE obs — 20260730

- UTC: `2026-07-30T19:53:12.250134+00:00`
- Regime: **bear**
- Expected Policy C file: `krw-btc-1h-ema-adx23-rsi55-sl3-tp45-m5-v6.json`
- Classifier file field: `strategies/krw-btc-1h-ema-adx23-rsi55-sl3-tp45-m5-v6.json`
- Match: **YES**
- SCALP LIVE: should be **OFF** (bitget stopped / profile scalp)
- Seed: **Upbit only** (ignore Bitget dust until ≥50만 total)
- Action: observe only — **do not** retune ADX/map

## Classifier JSON
```json
{
  "date": "2026-07-29",
  "regime": "bear",
  "close": 91424000.0,
  "sma50": 94557120.0,
  "sma200": 106512710.0,
  "adx": 28.01,
  "pdi": 13.08,
  "mdi": 29.6,
  "selected_file": "strategies/krw-btc-1h-ema-adx23-rsi55-sl3-tp45-m5-v6.json",
  "policy": "C_regime_v2",
  "engine": "v2",
  "bar": "closed",
  "live_trading": false
}
```

## Oracle snapshot
```
=== ps ===
bitget-futures-bot Exited (0) 7 hours ago
upbit-paper-bot Up 7 hours (healthy)
upbit-desk Up 35 hours (healthy)
upbit-edge Up 35 hours
=== STRATEGY ===
STRATEGY_PATH=/app/strategies/krw-btc-1h-ema-adx23-rsi55-sl3-tp45-m5-v6.json
=== upbit ===
======= 봇 상태 =======
시각: 2026-07-30 19:49:13
모드: 실주문
전략: KRW-BTC 1h EMA ADX23 RSI55 SL3/TP4.5 m5-v6
종목: 비트코인 (KRW-BTC)
봉간격: 1h
현재가: 91,509,000원
판단: 관망 — 매수/매도 조건 미충족
보유: 없음 (현금만 보유)
원화 잔고: 19,399원
BTC 잔고: 0

---- 주요 지표 ----
· ADX(추세강도): 9.0
· -DI(하락강도): 23.4
· +DI(상승강도): 20.0
· 장기 이평: 91,733,043
· 단기 이평: 91,694,950
=== bitget ===
bitget-futures-bot Exited (0) 7 hours ago
```

