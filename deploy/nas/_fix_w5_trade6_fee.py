"""ccxt reported the close fee as negative; store it positive and recompute trade 6 profit."""
import sqlite3

c = sqlite3.connect("/freqtrade/user_data/tradesv3-scalp-trend-short.sqlite")
o, cl, a, f = c.execute("select open_rate, close_rate, amount, fee_close_cost from trades where id=6").fetchone()
fee = abs(f)
p = (o - cl) * a - fee
c.execute("update trades set fee_close_cost=?, close_profit_abs=?, realized_profit=? where id=6", (fee, p, p))
c.commit()
print("trade6 profit_abs", round(p, 4), "fee", fee)
