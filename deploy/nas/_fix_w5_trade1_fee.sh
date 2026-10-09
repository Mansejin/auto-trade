#!/bin/sh
# w5: trade 1 (closed 2026-08-06 by liquidation, no exit fill) has an empty close fee, so freqtrade
# retries the fee update every 5s and floods the log. Mark the fee as known (0 USDT).
set -e
D="sudo -n /usr/local/bin/docker"
R=/volume1/docker/p3f8c1a2
DB=tradesv3-scalp-trend-short.sqlite
$D stop p3f8c1a2-w5
$D run --rm --entrypoint sh -v $R/freqtrade-research/user_data:/freqtrade/user_data freqtradeorg/freqtrade:stable -c "
cd /freqtrade/user_data && cp $DB $DB.bak-\$(date +%Y%m%d%H%M%S) && python3 - <<'PY'
import sqlite3
c = sqlite3.connect('$DB')
print('before', c.execute('select fee_open_cost,fee_open_currency,fee_close_cost,fee_close_currency from trades where id=1').fetchone())
c.execute(\"update trades set fee_close_cost=coalesce(fee_close_cost,0), fee_close_currency=coalesce(fee_close_currency,'USDT'), fee_open_cost=coalesce(fee_open_cost,0), fee_open_currency=coalesce(fee_open_currency,'USDT') where id=1\")
c.execute(\"update orders set ft_fee_base=coalesce(ft_fee_base,0) where ft_trade_id=1\")
c.commit()
print('after', c.execute('select fee_open_cost,fee_open_currency,fee_close_cost,fee_close_currency from trades where id=1').fetchone())
PY"
$D start p3f8c1a2-w5
echo started
