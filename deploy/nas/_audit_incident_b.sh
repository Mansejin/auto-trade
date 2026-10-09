#!/bin/sh
# Read-only: w5 fatal context, w1/w2 bot state, telegram failures. No secrets.
R=/volume1/docker/p3f8c1a2
F='key=|secret|token|passphrase|password|ACCESS-|bot[0-9]+:'
L="$R/freqtrade-research/user_data/logs/scalp-trend-short.log*"
echo "== w5 fatal context"
cat $L | grep -B3 -A40 'Fatal exception' | grep -viE "$F" | cut -c1-260 | head -n 60
echo "== w5 network warning"
cat $L | grep -A2 'fetch_positions() returned exception' | grep -viE "$F" | cut -c1-260
echo "== w5 start/stop events"
cat $L | grep -hE 'Changing state|Bot heartbeat|Starting worker|SIGTERM|Shutting down|cleanup' | grep -v heartbeat | sort | cut -c1-200 | tail -n 20
echo "== w1 telegram/alert/insufficient in logs (since 7d)"
sudo -n /usr/local/bin/docker logs --since 168h p3f8c1a2-w1 2>&1 | grep -iE 'telegram|알림|insufficient|InsufficientFunds|order fail|주문 실패|LIVE BUY|LIVE SELL|consecutive|연속' | grep -viE "$F" | cut -c1-220 | sed -E 's/[0-9]{2,}/N/g' | sort | uniq -c | sort -rn | head -n 20
echo "== w1 status.json / state / risk (non-secret)"
head -c 1500 $R/logs/status.json 2>/dev/null; echo
head -c 1500 $R/data/state.json 2>/dev/null; echo
head -c 800 $R/data/risk.json 2>/dev/null; echo
echo "== w2 state"; head -c 2000 $R/data/bitget_state.json; echo
echo "== w2 log signatures beyond status"
sudo -n /usr/local/bin/docker logs --since 168h p3f8c1a2-w2 2>&1 | grep -E '\| (WARNING|ERROR|INFO) \|' | grep -viE "$F|상태 요약|캔들 조회" | cut -c22- | sed -E 's/[0-9]{2,}/N/g' | cut -c1-200 | sort | uniq -c | sort -rn | head -n 20
echo "== w2 error timestamps"
sudo -n /usr/local/bin/docker logs --since 168h p3f8c1a2-w2 2>&1 | grep -E '\| ERROR \|' | cut -c1-120
echo "== w1 error timestamps"
sudo -n /usr/local/bin/docker logs --since 168h p3f8c1a2-w1 2>&1 | grep -E '\| ERROR \|' | cut -c1-120
echo "== strategies funding flags"
grep -l '"funding"' $R/strategies/*.json 2>/dev/null
python3 - <<'PY'
import json
for p in ("/volume1/docker/p3f8c1a2/strategies/bitget_btc_usdt_sma.json","/volume1/docker/p3f8c1a2/strategies/core-btc-sma200-filter-1d.json"):
    try:
        c=json.load(open(p,encoding="utf-8")); print(p, "funding", c.get("funding"), "keys", list(c)[:15])
    except Exception as e: print(p,"err",e)
PY
grep -E '^(PAPER|BITGET_PAPER|BITGET_STRATEGY_PATH|STRATEGY_PATH|LISTING_ALERT_DRY_RUN|TRANSFER_ENABLED|REBALANCE_ENABLED|POLL_SECONDS|BITGET_POLL_SECONDS)=' $R/.env
echo "== w6 telegram send results"
sudo -n /usr/local/bin/docker logs --since 168h p3f8c1a2-w6 2>&1 | grep -viE "announcements|market/all" | grep -viE "$F" | cut -c1-220 | sed -E 's/bot[^/]*\//bot<redacted>\//' | tail -n 30
ls -la $R/data | grep -iE 'listing|alert' 
echo "== host dns (resolv) + uptime"
uptime
