# pragma pylint: disable=missing-docstring, invalid-name
"""TrendShortV1 @ 3x with price-matched exits.

Keeps ~same price distance as 1x SL -3% / ROI +9%:
  at 3x, profit ratio SL -9% / ROI +27% ≈ 3% / 9% price (fees in).
"""
from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

from TrendShortV1Lev3 import TrendShortV1Lev3


class TrendShortV1Lev3Px(TrendShortV1Lev3):
    stoploss = -0.09
    minimal_roi = {"0": 0.27}


if __name__ == "__main__":
    assert TrendShortV1Lev3Px.stoploss == -0.09
    assert TrendShortV1Lev3Px.minimal_roi["0"] == 0.27
    assert (
        TrendShortV1Lev3Px.leverage(
            SimpleNamespace(),
            "BTC/USDT:USDT",
            datetime(2026, 1, 1),
            1.0,
            1.0,
            125.0,
            None,
            "short",
        )
        == 3.0
    )
