from __future__ import annotations

import logging

from bot.portfolio import Portfolio, Position, Trade, utc_now
from bot.signals import Signal

logger = logging.getLogger(__name__)


class PaperBroker:
    def __init__(self, fee_rate: float) -> None:
        self.fee_rate = fee_rate

    def execute(
        self,
        portfolio: Portfolio,
        *,
        market: str,
        signal: Signal,
        price: float,
        reason: str,
        buy_budget: float | None = None,
    ) -> Portfolio:
        if signal == Signal.BUY:
            return self._buy(
                portfolio, market=market, price=price, reason=reason, buy_budget=buy_budget
            )
        if signal in {Signal.SELL, Signal.STOP_LOSS, Signal.TAKE_PROFIT}:
            return self._sell(portfolio, market=market, price=price, reason=reason)
        return portfolio

    def _buy(
        self,
        portfolio: Portfolio,
        *,
        market: str,
        price: float,
        reason: str,
        buy_budget: float | None = None,
    ) -> Portfolio:
        if portfolio.in_position:
            logger.info("skip buy; already in position")
            return portfolio
        if portfolio.cash <= 0 or price <= 0:
            logger.warning("skip buy; cash=%.2f price=%.2f", portfolio.cash, price)
            return portfolio

        spend = portfolio.cash if buy_budget is None else min(portfolio.cash, max(0.0, buy_budget))
        if spend <= 0:
            logger.warning("skip buy; budget=%.2f", spend)
            return portfolio
        fee = spend * self.fee_rate
        qty = (spend - fee) / price
        portfolio.cash -= spend
        portfolio.position = Position(
            market=market,
            qty=qty,
            entry_price=price,
            opened_at=utc_now(),
        )
        portfolio.trades.append(
            Trade(
                ts=utc_now(),
                side="buy",
                market=market,
                price=price,
                qty=qty,
                fee=fee,
                reason=reason,
                paper=True,
            )
        )
        logger.info("PAPER BUY %s qty=%.8f price=%.2f fee=%.2f", market, qty, price, fee)
        return portfolio

    def _sell(self, portfolio: Portfolio, *, market: str, price: float, reason: str) -> Portfolio:
        if not portfolio.position:
            logger.info("skip sell; flat")
            return portfolio

        pos = portfolio.position
        proceeds = pos.qty * price
        fee = proceeds * self.fee_rate
        portfolio.cash += proceeds - fee
        portfolio.trades.append(
            Trade(
                ts=utc_now(),
                side="sell",
                market=market,
                price=price,
                qty=pos.qty,
                fee=fee,
                reason=reason,
                paper=True,
            )
        )
        logger.info(
            "PAPER SELL %s qty=%.8f price=%.2f fee=%.2f reason=%s",
            market,
            pos.qty,
            price,
            fee,
            reason,
        )
        portfolio.position = None
        return portfolio
