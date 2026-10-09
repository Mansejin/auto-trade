"""Read-only, inside w5: dump trades + orders (no secrets)."""
import sqlite3

db = sqlite3.connect("file:/freqtrade/user_data/tradesv3-scalp-trend-short.sqlite?mode=ro", uri=True)
db.row_factory = sqlite3.Row
cols = ("id,pair,is_open,is_short,leverage,amount,open_rate,close_rate,stake_amount,open_date,close_date,"
        "close_profit,close_profit_abs,realized_profit,exit_reason,stop_loss,initial_stop_loss,liquidation_price,"
        "stoploss_order_id" )
try:
    rows = db.execute(f"select {cols} from trades order by id").fetchall()
except Exception:
    rows = db.execute(f"select {cols.replace(',stoploss_order_id', '')} from trades order by id").fetchall()
for r in rows:
    print("trade", dict(r))
for r in db.execute("select ft_trade_id,ft_order_side,order_type,status,ft_is_open,order_id,price,average,stop_price,"
                    "amount,filled,order_date,order_filled_date,order_update_date from orders order by id"):
    print("order", dict(r))
