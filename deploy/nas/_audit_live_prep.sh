#!/bin/sh
# Read-only. Prints only short sha256 fingerprints of API keys, never the keys.
D="sudo -n /usr/local/bin/docker"
R=/volume1/docker/p3f8c1a2
UD=$R/freqtrade-research/user_data
echo "== key fingerprints"
python3 - <<'PY'
import hashlib, json, re
UD = "/volume1/docker/p3f8c1a2/freqtrade-research/user_data/"
fp = lambda s: hashlib.sha256((s or "").encode()).hexdigest()[:8] if s else "<empty>"
k = json.load(open(UD + "config.bitget-scalp.secrets.json")).get("exchange", {}).get("key")
print("w5 key", fp(k))
env = dict(re.findall(r"^([A-Z_]+)=(.*)$", open("/volume1/docker/p3f8c1a2/.env").read(), re.M))
print("w2 .env BITGET_API_KEY", fp(env.get("BITGET_API_KEY", "").strip().strip('"')))
print("TRANSFER_ENABLED", env.get("TRANSFER_ENABLED", "<unset>"), "BITGET_PAPER_CASH", env.get("BITGET_PAPER_CASH", "<unset>"))
c = json.load(open(UD + "config.bitget-scalp-trend-short-live.json"))
print("w5 order_types", c.get("order_types"), "stoploss", c.get("stoploss"), "trailing", c.get("trailing_stop"))
PY
echo "== w2 strategy"; cat $R/strategies/bitget_btc_usdt_sma.json
echo "== w5 log: stop/leverage events around trade 6"
grep -hE "2026-09-2[12].*(stoploss|Stoploss|leverage|Leverage|ERROR|WARNING)" $UD/logs/scalp-trend-short.log* 2>/dev/null | grep -viE "key|secret" | head -n 40
