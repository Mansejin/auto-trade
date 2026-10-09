#!/bin/sh
# w5: mark phantom stoploss orders (absent on exchange; Bitget UTA trigger orders unsupported) canceled.
set -e
D="sudo -n /usr/local/bin/docker"
R=/volume1/docker/p3f8c1a2
DB=tradesv3-scalp-trend-short.sqlite
$D stop p3f8c1a2-w5
$D run --rm --entrypoint sh -v $R/freqtrade-research/user_data:/freqtrade/user_data freqtradeorg/freqtrade:stable -c "
cd /freqtrade/user_data && cp $DB $DB.bak-\$(date +%Y%m%d%H%M%S) && python3 - <<'PY'
import sqlite3
c = sqlite3.connect('$DB')
n = c.execute(\"update orders set status='canceled', ft_is_open=0 where ft_is_open=1 and ft_order_side='stoploss'\").rowcount
c.commit()
print('updated', n)
for r in c.execute('select ft_order_side,status,ft_is_open,order_id,stop_price from orders where ft_trade_id=6'): print(r)
PY
ls -1 $DB.bak-* | tail -n 1"
$D start p3f8c1a2-w5
echo started
