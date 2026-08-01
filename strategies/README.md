# strategies

ConditionGroup JSON strategies for toolkit backtests and the paper bot.

## Active (regime policy B — current BEAR)
- slug: `krw-btc-1h-ema-adx23-obv-m5-v2`
- file: `krw-btc-1h-ema-adx23-obv-m5-v2.json`
- bot env: `STRATEGY_PATH=/app/strategies/krw-btc-1h-ema-adx23-obv-m5-v2.json`

Pointer file: `ACTIVE_STRATEGY`

## Deploy to server bot
```bash
# from a machine with SSH key access to ubuntu@129.225.205.185
./scripts/deploy-strategy-to-bot.sh krw-btc-1h-ema-adx23-obv-m5-v2
```
