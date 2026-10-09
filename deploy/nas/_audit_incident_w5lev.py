"""Read-only, inside w5: why leverage 20x? Inspect code paths + GET-only exchange calls. No secrets."""
import inspect
import json
import re

import ccxt
from freqtrade.exchange import bitget as ftb
from freqtrade.exchange import exchange as fte

print("ccxt", ccxt.__version__)
src = inspect.getsource(fte.Exchange._set_leverage)
print("--- Exchange._set_leverage\n", src[:2500])
for name in ("_set_leverage", "set_margin_mode", "_lev_prep", "get_max_leverage"):
    f = getattr(ftb.Bitget, name, None)
    if f is not None and name in ftb.Bitget.__dict__:
        print(f"--- Bitget.{name}\n", inspect.getsource(f)[:2000])
s = inspect.getsource(ccxt.bitget.set_leverage)
print("--- ccxt.bitget.set_leverage (uta branch lines)")
for ln in s.splitlines():
    if re.search(r"uta|Uta|def |privateMix|request\[|return", ln):
        print(ln)

UD = "/freqtrade/user_data/"
cfg = {}
for n in ("config.bitget-scalp-trend-short-live.json", "config.bitget-scalp.secrets.json"):
    cfg.update(json.load(open(UD + n, encoding="utf-8")).get("exchange", {}))
ex = ccxt.bitget({"apiKey": cfg.get("key"), "secret": cfg.get("secret"), "password": cfg.get("password"),
                  "options": {"defaultType": "swap", "uta": True}})
sym = "BTC/USDT:USDT"
ex.load_markets()
print("last", ex.fetch_ticker(sym)["last"])
for fn, args in (("fetch_leverage", (sym, {"marginMode": "isolated"})), ("fetch_positions", ([sym],))):
    try:
        r = getattr(ex, fn)(*args)
        if fn == "fetch_positions":
            r = [{k: p.get(k) for k in ("side", "contracts", "entryPrice", "markPrice", "leverage", "liquidationPrice",
                                         "unrealizedPnl", "marginMode", "initialMargin", "collateral")}
                 for p in r if float(p.get("contracts") or 0)]
        else:
            r = {k: r.get(k) for k in ("marginMode", "longLeverage", "shortLeverage")}
        print(fn, r)
    except Exception as e:
        print(fn, "err", type(e).__name__, str(e)[:300])
for m in ("privateUtaGetV3AccountSettings", "privateUtaGetV3AccountInfo"):
    if hasattr(ex, m):
        try:
            d = getattr(ex, m)({}).get("data")
            print(m, json.dumps(d)[:800])
        except Exception as e:
            print(m, "err", str(e)[:200])
try:
    d = ex.privateUtaGetV3AccountAssets({}).get("data") or {}
    print("assets", {k: d.get(k) for k in ("accountEquity", "usdtEquity", "unrealisedPnl")},
          [{k: a.get(k) for k in ("coin", "equity", "available", "locked")} for a in d.get("assets", []) if float(a.get("equity") or 0)])
except Exception as e:
    print("assets err", str(e)[:200])
try:
    d = ex.privateUtaGetV3TradeUnfilledStrategyOrders({"category": "USDT-FUTURES"}).get("data")
    print("pending_strategy", json.dumps(d)[:800])
except Exception as e:
    print("pending_strategy err", str(e)[:200])
try:
    d = ex.privateUtaGetV3TradeUnfilledOrders({"category": "USDT-FUTURES"}).get("data")
    print("pending_orders", json.dumps(d)[:800])
except Exception as e:
    print("pending_orders err", str(e)[:200])
try:
    d = ex.privateUtaGetV3TradeHistoryStrategyOrders({"category": "USDT-FUTURES", "type": "trigger"}).get("data")
    print("history_strategy", json.dumps(d)[:2500])
except Exception as e:
    print("history_strategy err", str(e)[:200])
