#!/bin/sh
# Read-only: grep freqtrade logfiles for leverage/stoploss/UTA/errors. No secrets.
R=/volume1/docker/p3f8c1a2/freqtrade-research/user_data
F='key=|secret|token|passphrase|password|ACCESS-|bot[0-9]+:'
ls -la $R/logs/ | head -n 30
ls -la $R/*.sqlite* $R/strategies/TrendShort* 2>&1
md5sum $R/strategies/TrendShortV1*.py
L="$R/logs/scalp-trend-short.log*"
echo "== range"; for f in $L; do echo "$f $(head -c 23 $f) .. $(tail -n1 $f | cut -c1-23)"; done
echo "== ERROR/WARNING signatures"
cat $L | grep -E ' - (ERROR|WARNING|CRITICAL) - ' | grep -viE "$F" | cut -c26- | sed -E 's/[0-9]{3,}/N/g' | cut -c1-220 | sort | uniq -c | sort -rn | head -n 40
echo "== leverage/margin lines"
cat $L | grep -iE 'leverage|40085|margin mode|set_margin|Unified|Classic' | grep -viE "$F|Using cached leverage" | cut -c1-300 | sort | uniq | head -n 40
echo "== stoploss lines (chronological sample)"
cat $L | grep -iE 'stoploss|stop loss|UTA trigger|StoplossOrder|does not exist' | grep -viE "$F" | cut -c1-300 | sort | head -n 80
echo "== stoploss lines tail"
cat $L | grep -iE 'stoploss|stop loss|UTA trigger|StoplossOrder|does not exist' | grep -viE "$F" | cut -c1-300 | sort | tail -n 40
echo "== entries/exits"
cat $L | grep -iE 'Entering|enter_short|Exit for|exit_reason|Selling|LIMIT_SELL|LIMIT_BUY|Order .* filled|Sending rpc message: \{.type.: (entry|exit)' | grep -viE "$F" | cut -c1-300 | sort | head -n 60
echo "== myTrade first occurrence"
grep -h -m1 'myTrade-dict empty' $L 2>/dev/null; for f in $L; do grep -c 'myTrade-dict empty' $f; done
echo "== config"
python3 - <<'PY'
import json
p="/volume1/docker/p3f8c1a2/freqtrade-research/user_data/config.bitget-scalp-trend-short-live.json"
c=json.load(open(p, encoding="utf-8"))
print({k:c.get(k) for k in ("dry_run","trading_mode","margin_mode","max_open_trades","stake_amount","tradable_balance_ratio","order_types","unfilledtimeout","stoploss","cancel_open_orders_on_exit")})
e=c.get("exchange",{}); print("exchange", {k:v for k,v in e.items() if k not in ("key","secret","password","uid")})
print("telegram enabled", c.get("telegram",{}).get("enabled"), "api_server", c.get("api_server",{}).get("enabled"))
PY
