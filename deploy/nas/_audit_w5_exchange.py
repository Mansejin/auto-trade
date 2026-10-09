"""Read-only: run inside w5. Compare exchange position + stop orders with the bot DB. No secrets printed."""
import json
import sqlite3

import ccxt

UD = "/freqtrade/user_data/"
ex_cfg = {}
for name in ("config.bitget-scalp-trend-short-live.json", "config.bitget-scalp.secrets.json"):
    ex_cfg.update(json.load(open(UD + name, encoding="utf-8")).get("exchange", {}))
ex = ccxt.bitget({
    "apiKey": ex_cfg.get("key"), "secret": ex_cfg.get("secret"), "password": ex_cfg.get("password"),
    "options": {"defaultType": "swap"},
})
sym = "BTC/USDT:USDT"
print("ticker", ex.fetch_ticker(sym)["last"])
for p in ex.fetch_positions([sym]):
    if float(p.get("contracts") or 0):
        print("position", {k: p.get(k) for k in ("side", "contracts", "entryPrice", "markPrice", "leverage",
                                                   "liquidationPrice", "unrealizedPnl", "marginMode", "initialMargin")})
print("ccxt", ccxt.__version__, "ccxt_config", {k: v for k, v in ex_cfg.get("ccxt_config", {}).items() if "key" not in k.lower()})
uta = [m for m in dir(ex) if m.lower().startswith("privateuta") and "strategy" in m.lower()]
print("uta_methods", uta)
for m in uta:
    if "get" in m.lower() and ("unfilled" in m.lower() or "pending" in m.lower()):
        try:
            print(m, json.dumps(getattr(ex, m)({"category": "USDT-FUTURES"}).get("data"))[:1500])
        except Exception as e:
            print(m, "err", str(e)[:200])
ex.options["uta"] = True
for fn, args in (("fetch_open_orders", (sym, None, None, {"trigger": True})),
                 ("fetch_order", ("1486065525176377361", sym, {"trigger": True}))):
    try:
        res = getattr(ex, fn)(*args)
        res = res if isinstance(res, list) else [res]
        print(fn, [{k: o.get(k) for k in ("id", "status", "side", "amount", "triggerPrice", "stopPrice", "reduceOnly")} for o in res])
    except Exception as e:
        print(fn, "err", type(e).__name__, str(e)[:200])

db = sqlite3.connect(UD + "tradesv3-scalp-trend-short.sqlite")
db.row_factory = sqlite3.Row
for r in db.execute("select ft_order_side, order_type, status, order_id, stop_price, amount, order_date "
                    "from orders where ft_trade_id=6 order by id"):
    print("db_order", dict(r))
