# pragma pylint: disable=missing-docstring, invalid-name
"""TrendShortV1 @ 3x leverage. Same di_cloud entry + SL -3% / ROI +9% (profit ratio).

freqtrade current_profit ≈ price_move × leverage (fees in), so at 3x:
  SL -3% ≈ ~1% adverse price
  ROI +9% ≈ ~3% favorable price
LIVE: do not swap until backtest review.
"""
from __future__ import annotations

from datetime import datetime

from TrendShortV1 import TrendShortV1


class TrendShortV1Lev3(TrendShortV1):
    def leverage(
        self,
        pair: str,
        current_time: datetime,
        current_rate: float,
        proposed_leverage: float,
        max_leverage: float,
        entry_tag: str | None,
        side: str,
        **kwargs,
    ) -> float:
        return min(3.0, max_leverage)


# ponytail: ceiling = lev hardcoded 3; upgrade via strategy param if we A/B more levers.
if __name__ == "__main__":
    from types import SimpleNamespace

    assert (
        TrendShortV1Lev3.leverage(
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
