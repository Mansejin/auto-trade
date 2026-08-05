"""Export OHLCV + TA-Lib indicators for cpp-bt (FT-aligned).

Format (little-endian):
  magic[8] = "FTIND001"
  u64 n
  repeated n:
    i64 ts_ms
    f64 open, high, low, close, volume
    f64 rsi, adx, plus_di, minus_di, cloud1, cloud2
"""
from __future__ import annotations

import argparse
import struct
from pathlib import Path

import numpy as np
import pandas as pd
import talib

MAGIC = b"FTIND001"
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FT = ROOT / "freqtrade-research" / "user_data" / "data"


def _ts_ms(dates: pd.Series) -> np.ndarray:
    t = pd.to_datetime(dates, utc=True)
    raw = t.astype("int64")
    if int(raw.iloc[0]) > 10**14:
        return (raw // 10**6).to_numpy()
    return raw.to_numpy()


def export(src: Path, dst: Path) -> int:
    df = pd.read_feather(src).sort_values("date").reset_index(drop=True)
    close = df["close"].to_numpy(dtype=np.float64)
    high = df["high"].to_numpy(dtype=np.float64)
    low = df["low"].to_numpy(dtype=np.float64)
    df["rsi"] = talib.RSI(close, 14)
    df["adx"] = talib.ADX(high, low, close, 14)
    df["plus_di"] = talib.PLUS_DI(high, low, close, 14)
    df["minus_di"] = talib.MINUS_DI(high, low, close, 14)
    hh9 = df["high"].rolling(9).max()
    ll9 = df["low"].rolling(9).min()
    hh26 = df["high"].rolling(26).max()
    ll26 = df["low"].rolling(26).min()
    hh52 = df["high"].rolling(52).max()
    ll52 = df["low"].rolling(52).min()
    tenkan = (hh9 + ll9) / 2.0
    kijun = (hh26 + ll26) / 2.0
    span1 = (tenkan + kijun) / 2.0
    span2 = (hh52 + ll52) / 2.0
    df["cloud1"] = span1.shift(26)
    df["cloud2"] = span2.shift(26)

    ts = _ts_ms(df["date"])
    n = len(df)
    dst.parent.mkdir(parents=True, exist_ok=True)
    nan = float("nan")
    with dst.open("wb") as f:
        f.write(MAGIC)
        f.write(struct.pack("<Q", n))
        for i in range(n):
            row = df.iloc[i]
            def f64(v):
                x = float(v)
                return nan if x != x else x

            f.write(
                struct.pack(
                    "<qddddddddddd",
                    int(ts[i]),
                    float(row["open"]),
                    float(row["high"]),
                    float(row["low"]),
                    float(row["close"]),
                    float(row["volume"]),
                    f64(row["rsi"]),
                    f64(row["adx"]),
                    f64(row["plus_di"]),
                    f64(row["minus_di"]),
                    f64(row["cloud1"]),
                    f64(row["cloud2"]),
                )
            )
    return n


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--exchange", default="bitget")
    p.add_argument("--symbol", default="BTC_USDT_USDT")
    p.add_argument("--timeframe", default="5m")
    p.add_argument("--data-root", type=Path, default=DEFAULT_FT)
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()
    src = (
        args.data_root
        / args.exchange
        / "futures"
        / f"{args.symbol}-{args.timeframe}-futures.feather"
    )
    if not src.exists():
        raise SystemExit(f"not found: {src}")
    out = args.out or (ROOT / "cpp-bt" / "data" / f"{args.symbol}-{args.timeframe}.ftind")
    n = export(src, out)
    print(f"wrote {out} rows={n}")


if __name__ == "__main__":
    main()
