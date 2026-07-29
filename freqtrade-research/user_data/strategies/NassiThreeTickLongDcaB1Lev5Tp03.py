# pragma pylint: disable=missing-docstring, invalid-name
"""나씨 3틱 B + leverage 5 + reclaim TP 3%.

Card: docs/research/nassi-3tick-b-lev5-tp-card-frozen.md
"""
from __future__ import annotations

from datetime import datetime

from freqtrade.persistence import Trade

from NassiThreeTickLongDcaB1 import NassiThreeTickLongDcaB1


class NassiThreeTickLongDcaB1Lev5Tp03(NassiThreeTickLongDcaB1):
    reclaim_pct = 0.03

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
        return min(5.0, max_leverage)

    def custom_exit(
        self,
        pair: str,
        trade: Trade,
        current_time: datetime,
        current_rate: float,
        current_profit: float,
        **kwargs,
    ) -> str | bool | None:
        if current_profit >= self.reclaim_pct:
            return "avg_reclaim"
        return None


class NassiThreeTickLongDcaB1Lev5Tp05(NassiThreeTickLongDcaB1Lev5Tp03):
    reclaim_pct = 0.05


if __name__ == "__main__":
    assert NassiThreeTickLongDcaB1Lev5Tp03.reclaim_pct == 0.03
    assert NassiThreeTickLongDcaB1Lev5Tp05.reclaim_pct == 0.05
    print("NassiThreeTickLongDcaB1Lev5Tp OK")
