"""Export Freqtrade feather OHLCV to cpp-bt packed binary (.ohlcv).

Format (little-endian):
  magic[8] = "OHLCV001"
  u64 n
  repeated n:
    i64 ts_ms (UTC)
    f64 open, high, low, close, volume
"""
from __future__ import annotations

import argparse
import struct
from pathlib import Path

import pandas as pd

MAGIC = b"OHLCV001"
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FT = ROOT / "freqtrade-research" / "user_data" / "data"


def export(src: Path, dst: Path) -> int:
    df = pd.read_feather(src)
    need = {"date", "open", "high", "low", "close", "volume"}
    missing = need - set(df.columns)
    if missing:
        raise SystemExit(f"missing columns {missing} in {src}")
    df = df.sort_values("date")
    t = pd.to_datetime(df["date"], utc=True)
    raw = t.astype("int64")
    # feather may be datetime64[ms] (already ms) or [ns]
    if int(raw.iloc[0]) > 10**14:
        ts = (raw // 10**6).to_numpy()
    else:
        ts = raw.to_numpy()
    rows = len(df)
    dst.parent.mkdir(parents=True, exist_ok=True)
    with dst.open("wb") as f:
        f.write(MAGIC)
        f.write(struct.pack("<Q", rows))
        for i in range(rows):
            f.write(
                struct.pack(
                    "<qddddd",
                    int(ts[i]),
                    float(df["open"].iloc[i]),
                    float(df["high"].iloc[i]),
                    float(df["low"].iloc[i]),
                    float(df["close"].iloc[i]),
                    float(df["volume"].iloc[i]),
                )
            )
    return rows


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--exchange", default="bitget")
    p.add_argument("--market", default="futures", choices=("futures", "spot"))
    p.add_argument("--symbol", default="BTC_USDT_USDT")
    p.add_argument("--timeframe", default="5m")
    p.add_argument("--data-root", type=Path, default=DEFAULT_FT)
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()

    kind = "futures" if args.market == "futures" else ""
    name = f"{args.symbol}-{args.timeframe}"
    if args.market == "futures":
        name += "-futures"
    src = args.data_root / args.exchange / ("futures" if args.market == "futures" else "") / f"{name}.feather"
    # spot path fallback
    if args.market == "spot":
        src = args.data_root / args.exchange / f"{args.symbol}-{args.timeframe}.feather"
    if not src.exists():
        raise SystemExit(f"not found: {src}")
    out = args.out or (ROOT / "cpp-bt" / "data" / f"{args.symbol}-{args.timeframe}.ohlcv")
    n = export(src, out)
    print(f"wrote {out} rows={n}")


if __name__ == "__main__":
    main()
