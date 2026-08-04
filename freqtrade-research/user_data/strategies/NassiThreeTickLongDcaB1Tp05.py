# pragma pylint: disable=missing-docstring, invalid-name
"""나씨 3틱 B + reclaim TP 0.5%.

Card: docs/research/nassi-3tick-b-tp05-card-frozen.md
"""
from __future__ import annotations

from datetime import datetime

from freqtrade.persistence import Trade

from NassiThreeTickLongDcaB1 import NassiThreeTickLongDcaB1


class NassiThreeTickLongDcaB1Tp05(NassiThreeTickLongDcaB1):
    # exit constant (card delta) — not a hyper
    reclaim_pct = 0.005

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


if __name__ == "__main__":
    assert NassiThreeTickLongDcaB1Tp05.reclaim_pct == 0.005
    print("NassiThreeTickLongDcaB1Tp05 self-check OK")
