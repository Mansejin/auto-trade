"""Read-only: run inside w5. Where did the bot's stop order go? No secrets printed."""
import json

import ccxt

UD = "/freqtrade/user_data/"
ex_cfg = {}
for name in ("config.bitget-scalp-trend-short-live.json", "config.bitget-scalp.secrets.json"):
    ex_cfg.update(json.load(open(UD + name, encoding="utf-8")).get("exchange", {}))
ex = ccxt.bitget({"apiKey": ex_cfg.get("key"), "secret": ex_cfg.get("secret"), "password": ex_cfg.get("password"),
                  "options": {"defaultType": "swap", "uta": True}})
r = ex.privateUtaGetV3TradeHistoryStrategyOrders({"category": "USDT-FUTURES", "symbol": "BTCUSDT", "limit": "20"})
rows = (r.get("data") or {}).get("list") or r.get("data") or []
for o in rows if isinstance(rows, list) else []:
    print({k: o.get(k) for k in ("orderId", "side", "qty", "triggerPrice", "status", "strategyType",
                                 "posSide", "createdTime", "updatedTime", "cancelReason")})
print("raw_keys", list((r.get("data") or {}).keys()) if isinstance(r.get("data"), dict) else type(r.get("data")))
