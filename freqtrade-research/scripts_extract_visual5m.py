import json
import zipfile
from pathlib import Path

import pandas as pd

root = Path("user_data")
zips = sorted(
    (root / "backtest_results").glob("backtest-result-*.zip"),
    key=lambda p: p.stat().st_mtime,
)
picked = None
strat_name = None
for z in reversed(zips[-20:]):
    with zipfile.ZipFile(z) as zf:
        names = zf.namelist()
        data_name = [n for n in names if n.endswith(".json") and "meta" not in n]
        if not data_name:
            continue
        data = json.loads(zf.read(data_name[0]))
        strategies = data.get("strategy") or {}
        for name in ("Visual5mBearShortV2", "Visual5mBearShortV1"):
            if name in strategies:
                picked = z
                strat_name = name
                break
    if picked:
        break

if not picked:
    raise SystemExit("no visual 5m backtest found")

print("picked", picked, strat_name)
with zipfile.ZipFile(picked) as zf:
    data_name = [n for n in zf.namelist() if n.endswith(".json") and "meta" not in n][0]
    data = json.loads(zf.read(data_name))

trades = data["strategy"][strat_name]["trades"]
rows = []
for t in trades:
    rows.append(
        {
            "open": t.get("open_date"),
            "profit_pct": round(float(t.get("profit_ratio", 0)) * 100, 3),
            "profit_abs": round(float(t.get("profit_abs", 0)), 3),
            "dur_min": t.get("trade_duration"),
            "exit": t.get("exit_reason"),
        }
    )

df = pd.DataFrame(rows)
df["open_ts"] = pd.to_datetime(df["open"])
df = df.sort_values("open_ts")
gaps = df["open_ts"].diff().dt.total_seconds() / 60.0
by_hour = df.groupby(df["open_ts"].dt.floor("h")).size()
span_days = max(
    (df["open_ts"].max() - df["open_ts"].min()).total_seconds() / 86400, 1e-9
)

# raw signal density on same window
feather = root / "data/bitget/futures/ETH_USDT_USDT-5m-futures.feather"
raw = {"n": None, "median_gap_min": None, "per_day": None}
if feather.exists():
    import talib

    cdf = pd.read_feather(feather)
    start, end = df["open_ts"].min(), df["open_ts"].max() + pd.Timedelta(hours=1)
    cdf = cdf[(cdf["date"] >= start) & (cdf["date"] <= end)].copy()
    cdf["ema21"] = talib.EMA(cdf["close"], 21)
    cdf["ema55"] = talib.EMA(cdf["close"], 55)
    cdf["rsi"] = talib.RSI(cdf["close"], 14)
    sig = (
        (cdf["ema21"] < cdf["ema55"])
        & (cdf["close"] < cdf["open"])
        & (cdf["close"] < cdf["ema21"])
        & (cdf["rsi"] < 55)
    )
    sdates = cdf.loc[sig, "date"]
    sgap = sdates.diff().dt.total_seconds() / 60.0
    raw = {
        "n": int(sig.sum()),
        "median_gap_min": round(float(sgap.median()), 1) if len(sgap) > 1 else None,
        "per_day": round(float(sig.sum()) / max(span_days, 1e-9), 1),
    }

out = {
    "strategy": strat_name,
    "pair": "ETH/USDT:USDT",
    "timeframe": "5m",
    "fee": "0.06% taker each way",
    "purpose": "Visual dense short scalp — not fee-surviving. Paper only.",
    "rules": {
        "entry": "EMA21<EMA55 AND bearish candle AND close<EMA21 AND RSI<55",
        "exit": "ROI +0.20% / SL -0.12%",
    },
    "filled_trades": {
        "n": int(len(df)),
        "trades_per_day": round(len(df) / span_days, 1),
        "median_gap_min": round(float(gaps.median()), 1) if len(gaps) > 1 else None,
        "mean_gap_min": round(float(gaps.mean()), 1) if len(gaps) > 1 else None,
        "avg_hold_min": round(float(df["dur_min"].mean()), 1),
        "wins": int((df["profit_pct"] > 0).sum()),
        "losses": int((df["profit_pct"] <= 0).sum()),
        "net_usdt": round(float(df["profit_abs"].sum()), 2),
        "pf_approx": None,
    },
    "raw_signals": raw,
    "trades_per_hour": [
        {"t": h.strftime("%m-%d %H:%M"), "n": int(n)} for h, n in by_hour.items()
    ],
    "recent_trades": [
        {
            "open": r.open_ts.strftime("%m-%d %H:%M"),
            "profit_pct": r.profit_pct,
            "dur_min": r.dur_min,
            "exit": r.exit,
            "tone": "success" if r.profit_pct > 0 else "danger",
        }
        for r in df.sort_values("open_ts", ascending=False).head(40).itertuples()
    ],
    "equity": [],
}

eq = 1000.0
for r in df.itertuples():
    eq += r.profit_abs
    out["equity"].append(
        {"t": r.open_ts.strftime("%m-%d %H:%M"), "equity": round(eq, 2)}
    )

# rough PF
wins = df.loc[df["profit_abs"] > 0, "profit_abs"].sum()
loss = -df.loc[df["profit_abs"] < 0, "profit_abs"].sum()
out["filled_trades"]["pf_approx"] = round(float(wins / loss), 2) if loss else None

path = root / "visual5m_summary.json"
path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("wrote", path)
print(json.dumps({"filled": out["filled_trades"], "raw": out["raw_signals"]}, indent=2))
