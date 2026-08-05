"""In-process Freqtrade backtest for param grids.

Loads candles once per timerange, re-advises only when entry params change,
then reuses the processed frame across SL/ROI/trailing variants.

Much faster than spawning `freqtrade.exe` per combo (~2s vs ~10s per window).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

ROOT = Path(__file__).resolve().parents[1]
FT = ROOT / "freqtrade-research"


@dataclass(frozen=True)
class ExitParams:
    stoploss: float
    roi: float
    trailing: bool = False
    trail_pos: float | None = None
    trail_offset: float | None = None


@dataclass(frozen=True)
class WindowResult:
    trades: int
    profit_factor: float | None
    profit_pct: float | None


def _pf(trades) -> tuple[int, float | None, float | None]:
    n = len(trades)
    if n == 0:
        return 0, None, None
    wins = float(trades.loc[trades["profit_ratio"] > 0, "profit_abs"].sum())
    loss = float(abs(trades.loc[trades["profit_ratio"] <= 0, "profit_abs"].sum()))
    pf = (wins / loss) if loss > 0 else None
    # rough total return proxy (sum of trade ratios); fine for ranking
    pct = float(trades["profit_ratio"].sum()) * 100.0
    return n, pf, pct


class FtGrid:
    """One Backtesting instance + cached advise per entry-key."""

    def __init__(
        self,
        config_path: Path | str,
        strategy: str,
        timerange: str,
        *,
        strategy_path: Path | str | None = None,
    ) -> None:
        logging.getLogger("freqtrade").setLevel(logging.ERROR)
        logging.getLogger("numexpr").setLevel(logging.ERROR)

        from freqtrade.configuration import Configuration
        from freqtrade.optimize.backtesting import Backtesting

        cfg_path = Path(config_path)
        if not cfg_path.is_absolute():
            cfg_path = FT / cfg_path
        # FT resolves user_data_dir relative to cwd — pin to research root
        import os

        os.chdir(FT)
        config = Configuration.from_files([str(cfg_path)])
        if hasattr(config, "get_config"):
            config = config.get_config()
        config = dict(config)
        config["timerange"] = timerange
        config["export"] = "none"
        config["strategy"] = strategy
        config["cache"] = "none"
        config["verbosity"] = 0
        if strategy_path is not None:
            config["strategy_path"] = str(strategy_path)

        self._bt = Backtesting(config)
        self._data, self._timerange = self._bt.load_bt_data()
        self._strat = self._bt.strategylist[0]
        self._bt._set_strategy(self._strat)
        self._advise_key: Any = None
        self._pre = None
        self._min_date = None
        self._max_date = None

    def _ensure_advise(self, apply_entry: Callable[[Any], Any]) -> None:
        from freqtrade.data.history import get_timerange
        from freqtrade.optimize.backtesting import trim_dataframes

        key = apply_entry(self._strat)
        if key == self._advise_key and self._pre is not None:
            return
        self._pre = self._strat.advise_all_indicators(self._data)
        pre_tmp = trim_dataframes(self._pre, self._timerange, self._bt.required_startup)
        self._min_date, self._max_date = get_timerange(pre_tmp)
        self._advise_key = key

    def run(
        self,
        apply_entry: Callable[[Any], Any],
        exit_params: ExitParams,
    ) -> WindowResult:
        self._ensure_advise(apply_entry)
        s = self._strat
        s.stoploss = float(exit_params.stoploss)
        s.minimal_roi = {0: float(exit_params.roi)}
        s.trailing_stop = bool(exit_params.trailing)
        if exit_params.trailing:
            s.trailing_stop_positive = float(exit_params.trail_pos or 0.0)
            s.trailing_stop_positive_offset = float(exit_params.trail_offset or 0.0)
            s.trailing_only_offset_is_reached = True
        else:
            s.trailing_stop_positive = None
            s.trailing_stop_positive_offset = 0.0
            s.trailing_only_offset_is_reached = False

        self._bt.reset_backtest()
        res = self._bt.backtest(
            processed=self._pre,
            start_date=self._min_date,
            end_date=self._max_date,
        )
        n, pf, pct = _pf(res["results"])
        return WindowResult(n, pf, pct)


def run_windows(
    grids: dict[str, FtGrid],
    apply_entry: Callable[[Any], Any],
    exit_params: ExitParams,
) -> dict[str, WindowResult]:
    return {name: g.run(apply_entry, exit_params) for name, g in grids.items()}


# ponytail: smoke — module imports & ExitParams hashable
if __name__ == "__main__":
    e = ExitParams(-0.01, 0.03, True, 0.01, 0.02)
    assert e.trailing and e.stoploss < 0
    print("ok", e)
