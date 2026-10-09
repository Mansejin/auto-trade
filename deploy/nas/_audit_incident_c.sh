#!/bin/sh
# Read-only: w6 telegram sends (token redacted), state. No secrets.
R=/volume1/docker/p3f8c1a2
D="sudo -n /usr/local/bin/docker"
echo "== w6 telegram lines"
$D logs --since 168h p3f8c1a2-w6 2>&1 | grep -iE 'telegram|sendMessage|send|alert|listing' | grep -vE 'announcements\?|market/all' \
  | sed -E 's#bot[0-9]+:[A-Za-z0-9_-]+#bot<redacted>#g; s#chat_id=[-0-9]+#chat_id=<redacted>#g' | cut -c1-220 | tail -n 30
echo "== w6 around KAIA"
$D logs --since 168h p3f8c1a2-w6 2>&1 | grep -B4 -A8 'KAIAUSDT' | grep -vE 'market/all' \
  | sed -E 's#bot[0-9]+:[A-Za-z0-9_-]+#bot<redacted>#g' | cut -c1-220 | head -n 30
echo "== w6 state"
python3 - <<'PY'
import json
d=json.load(open("/volume1/docker/p3f8c1a2/data/listing-alert-state.json",encoding="utf-8"))
print(json.dumps(d, ensure_ascii=False)[:1500])
PY
echo "== w1 telegram"
$D logs --since 168h p3f8c1a2-w1 2>&1 | grep -iE 'telegram|getUpdates|sendMessage' | sed -E 's#bot[0-9]+:[A-Za-z0-9_-]+#bot<redacted>#g' | cut -c1-200 | sed -E 's/[0-9]{2,}/N/g' | sort | uniq -c | sort -rn | head -n 10
echo "== w1 balance history"
$D logs --since 168h p3f8c1a2-w1 2>&1 | grep -E '잔고 조회 성공|실주문|LIVE (BUY|SELL) ' | cut -c1-200 | head -n 10
echo "== w1 trades log"
ls -la $R/logs | head -n 30
tail -n 15 $R/logs/trades.log 2>/dev/null | cut -c1-200
