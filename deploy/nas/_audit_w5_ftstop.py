"""Read-only, inside w5: fetch the stop order exactly the way freqtrade does."""
import sqlite3

from freqtrade.configuration import Configuration
from freqtrade.enums import RunMode
from freqtrade.resolvers import ExchangeResolver

UD = "/freqtrade/user_data/"
cfg = Configuration.from_files([UD + "config.bitget-scalp-trend-short-live.json", UD + "config.bitget-scalp.secrets.json"])
cfg["runmode"] = RunMode.UTIL_EXCHANGE
ex = ExchangeResolver.load_exchange(cfg, validate=False, load_leverage_tiers=False)
oid = sqlite3.connect(UD + "tradesv3-scalp-trend-short.sqlite").execute(
    "select order_id from orders where ft_trade_id=6 and ft_order_side='stoploss' and ft_is_open=1").fetchone()[0]
o = ex.fetch_stoploss_order(oid, "BTC/USDT:USDT")
print({k: o.get(k) for k in ("id", "status", "type", "side", "amount", "stopPrice", "triggerPrice", "reduceOnly")})
print("info", {k: o.get("info", {}).get(k) for k in ("orderId", "status", "planStatus", "planType", "triggerPrice", "type", "category", "side", "posSide")})
