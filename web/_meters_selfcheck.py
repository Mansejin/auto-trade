"""ponytail: one check for condition-meter mapping. run: python web/_meters_selfcheck.py"""
from __future__ import annotations

from condition_meters import (
    build_condition_meters,
    cond_met,
    meters_from_trend_short_snap,
    meter_scale,
)


def main() -> None:
    assert cond_met("gt", 30, 23) is True
    assert cond_met("lt", 48, 55) is True
    assert cond_met("lt", 60, 55) is False
    lo, hi = meter_scale("rsi14.rsi", 48, 55)
    assert lo == 0 and hi == 100

    status = {
        "strategy_file": "krw-btc-1h-ema-adx23-rsi55-sl3-tp45-m5-v6.json",
        "values": {
            "ma_short.value": 91000000,
            "ma_long.value": 90500000,
            "adx14.adx": 32,
            "rsi14.rsi": 48,
        },
    }
    meters = build_condition_meters(status)
    kinds = {m["kind"] for m in meters}
    assert "threshold" in kinds
    assert "compare" in kinds
    adx = next(m for m in meters if m["label"] == "ADX" and m["side"] == "buy")
    assert adx["met"] is True and adx["threshold"] == 23
    rsi = next(m for m in meters if m["label"] == "RSI" and m["side"] == "buy")
    assert rsi["met"] is True and rsi["threshold"] == 55

    ts = meters_from_trend_short_snap(
        {
            "close": 64000,
            "adx": 20,
            "plus_di": 10,
            "minus_di": 18,
            "cloud1": 65000,
            "cloud2": 65500,
        },
        adx_min=15,
    )
    assert len(ts) == 4
    assert all(m["side_label"] == "숏진입" for m in ts)
    assert all(m["met"] is True for m in ts)
    print(f"ok meters={len(meters)} trend_short={len(ts)}")


if __name__ == "__main__":
    main()
