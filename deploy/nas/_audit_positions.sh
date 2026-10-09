#!/bin/sh
# Read-only: container modes + open positions. Prints no secret values.
D="sudo -n /usr/local/bin/docker"
R=/volume1/docker/p3f8c1a2
echo "== containers"
$D ps --format '{{.Names}} {{.Status}}' | grep p3f8c1a2
echo "== .env mode keys (values for non-secret keys only)"
grep -E '^(PAPER|BITGET_PAPER|BITGET_PAPER_TRADING|EXCHANGE|STRATEGY_PATH|BITGET_STRATEGY_PATH|BITGET_CATEGORY|BITGET_ORDER_FRACTION|BITGET_MAX_ORDER_USDT)=' $R/.env
grep -qE '^LIVE_CONFIRM=I_UNDERSTAND' $R/.env && echo "LIVE_CONFIRM=<set>" || echo "LIVE_CONFIRM=<missing>"
for c in w1 w2; do
  echo "== $c runtime env"
  $D exec p3f8c1a2-$c sh -c 'echo PAPER=$PAPER EXCHANGE=$EXCHANGE BITGET_PAPER_TRADING=$BITGET_PAPER_TRADING STRATEGY=$STRATEGY_PATH; [ -n "$LIVE_CONFIRM" ] && echo LIVE_CONFIRM=set || echo LIVE_CONFIRM=empty; [ -n "$BITGET_API_KEY" ] && echo BITGET_KEY=set || echo BITGET_KEY=empty'
done
echo "== w1 latest_status"; tail -n 25 $R/logs/latest_status.txt 2>/dev/null
echo "== w2 latest_status"; tail -n 25 $R/logs/bitget/latest_status.txt 2>/dev/null
echo "== w2 state"; cat $R/data/bitget_state.json 2>/dev/null | head -c 2500; echo
echo "== w2 log tail"; $D logs --tail 25 p3f8c1a2-w2 2>&1
echo "== w5 freqtrade config"
python3 - <<'PY'
import json
p="/volume1/docker/p3f8c1a2/freqtrade-research/user_data/config.bitget-scalp-trend-short-live.json"
try:
    c=json.load(open(p))
    print({k:c.get(k) for k in ("dry_run","trading_mode","margin_mode","max_open_trades","stake_amount","stake_currency","tradable_balance_ratio")})
    print("pairs", c.get("exchange",{}).get("pair_whitelist"))
except Exception as e: print("config err", e)
PY
echo "== w5 open trades"
$D exec p3f8c1a2-w5 python3 -c "
import sqlite3
c=sqlite3.connect('/freqtrade/user_data/tradesv3-scalp-trend-short.sqlite'); c.row_factory=sqlite3.Row
for r in c.execute('select id,pair,is_short,amount,open_rate,stake_amount,leverage,stop_loss,liquidation_price,open_date,enter_tag from trades where is_open=1'): print(dict(r))
print('closed_last5')
for r in c.execute('select id,pair,is_short,open_date,close_date,close_profit,exit_reason from trades where is_open=0 order by id desc limit 5'): print(dict(r))
"
echo "== w5 log tail"; $D logs --tail 30 p3f8c1a2-w5 2>&1 | grep -viE 'key|secret|token' | tail -n 30
