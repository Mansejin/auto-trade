"""w5 is stopped. Trade 6 was closed manually on Bitget: record the real fill in the freqtrade DB."""
import json
import shutil
import sqlite3
import time
from datetime import datetime, timezone

import ccxt

UD = "/freqtrade/user_data/"
DB = UD + "tradesv3-scalp-trend-short.sqlite"
ex_cfg = {}
for name in ("config.bitget-scalp-trend-short-live.json", "config.bitget-scalp.secrets.json"):
    ex_cfg.update(json.load(open(UD + name, encoding="utf-8")).get("exchange", {}))
ex = ccxt.bitget({"apiKey": ex_cfg.get("key"), "secret": ex_cfg.get("secret"), "password": ex_cfg.get("password"),
                  "options": {"defaultType": "swap", "uta": True}})
sym = "BTC/USDT:USDT"
assert not [p for p in ex.fetch_positions([sym]) if float(p.get("contracts") or 0)], "position still open"
fills = [t for t in ex.fetch_my_trades(sym, since=int(time.time() * 1000) - 3 * 3600 * 1000) if t["side"] == "buy"]
assert fills, "no recent buy fill found"
qty = sum(t["amount"] for t in fills)
px = sum(t["amount"] * t["price"] for t in fills) / qty
fee = sum((t.get("fee") or {}).get("cost") or 0 for t in fills)
ts = max(t["timestamp"] for t in fills)
print("fills", len(fills), "qty", qty, "avg", round(px, 1), "fee", fee, "at", datetime.fromtimestamp(ts / 1000, timezone.utc))

shutil.copy(DB, DB + ".bak-" + time.strftime("%Y%m%d%H%M%S"))
c = sqlite3.connect(DB)
open_rate, amount = c.execute("select open_rate, amount from trades where id=6 and is_open=1").fetchone()
profit_abs = (open_rate - px) * amount - fee
close_date = datetime.fromtimestamp(ts / 1000, timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")
c.execute("update trades set is_open=0, close_rate=?, close_date=?, exit_reason='manual_exchange', "
          "close_profit_abs=?, realized_profit=?, fee_close_cost=?, fee_close_currency='USDT' where id=6",
          (px, close_date, profit_abs, profit_abs, fee))
c.commit()
print("trade6 closed in DB, profit_abs", round(profit_abs, 4))
print("usdt", ex.fetch_balance().get("USDT", {}).get("total"))
