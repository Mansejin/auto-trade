# Notes — kimchi-rich-preposition-skip-v1

Not part of ConditionGroup JSON. Capital routing / external signals.

## Hypothesis

When Upbit KRW-BTC premium ≥ 0.004563 (AE13 train 90th, frozen), skip new Upbit spot longs; prefer capital already on Bitget USDT. Bridge = rare rebalance, not HFT arb.

## External signal (bot/ops layer)

- Rich premium → suppress Upbit buys even if JSON buy=true (not yet wired; paper-log AE14).
- ConditionGroup alone does **not** encode premium.

## Capital routing

- Idle: 50:50 ±12%p; suggest-only until `/리밸런스승인`
- U→B / B→U: band breach + cooldown + REBALANCE_MIN_MOVE_KRW; B→U needs TRX ≥ minWithdraw≈27.7 + fee≈1.1
- Do not relocate for few bps of premium

## Falsify

See chat / AE13 / AE14 paper-log spec (cost, delay, min withdraw).
