"""Bitget USDT-M futures tick (paper + gated LIVE)."""

from __future__ import annotations

import logging
import time
import uuid

from bot.broker import PaperBroker
from bot.config import Settings
from bot.display import format_status_block, fmt_money, fmt_qty
from bot.indicators import OHLCV
from bot.logging_setup import write_latest_status, write_status_json
from bot.portfolio import Position, Trade, utc_now
from bot.risk import (
    allow_buy,
    allow_sell,
    check_daily_loss,
    load_risk,
    record_success,
    refresh_day,
    save_risk,
)
from bot.bitget_client import BitgetPrivate, BitgetPublic
from bot.signals import Signal, evaluate
from bot.state_store import load_state, save_state
from bot.strategy_loader import load_strategy
from bot.telegram_notify import TelegramNotifier, format_buy_alert, format_sell_alert

logger = logging.getLogger("bot.bitget")


def _closed_bar_key(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    return str(rows[-1][0])


def _buy_budget_usdt(cash: float, settings: Settings) -> float:
    budget = cash * settings.order_fraction
    if settings.max_order_krw > 0:
        # reuse MAX_ORDER_KRW as max notional in quote currency (USDT) for Bitget
        budget = min(budget, settings.max_order_krw)
    return max(0.0, budget)


def run_once_bitget(settings: Settings, trades: logging.Logger, notify: TelegramNotifier) -> None:
    strategy = load_strategy(settings.strategy_path)
    mode = "PAPER" if settings.paper else "LIVE"
    symbol = strategy.market.upper().replace("-", "").replace("USDTM", "USDT")
    if not symbol.endswith("USDT"):
        # allow BTCUSDT already; if user put BTC-USDT normalize
        if "USDT" not in symbol:
            symbol = f"{symbol}USDT"

    public = BitgetPublic()
    private: BitgetPrivate | None = None

    try:
        if not settings.paper:
            if not settings.live_allowed:
                raise RuntimeError(
                    "LIVE Bitget 설정 부족 — BITGET_API_KEY/SECRET/PASSPHRASE + "
                    "LIVE_CONFIRM=I_UNDERSTAND_LIVE_TRADING_RISK 필요"
                )
            private = BitgetPrivate(
                settings.bitget_api_key,
                settings.bitget_secret_key,
                settings.bitget_passphrase,
            )

        logger.info(
            "Bitget 캔들 조회… symbol=%s tf=%s product=%s",
            symbol,
            strategy.timeframe,
            settings.bitget_product_type,
        )
        rows = public.candles(
            symbol,
            strategy.timeframe,
            product_type=settings.bitget_product_type,
            limit=200,
        )
        if len(rows) < 30:
            raise RuntimeError(f"insufficient candles: {len(rows)}")
        ohlcv = OHLCV.from_bitget_candles(rows)
        bar_key = _closed_bar_key(rows)
        logger.info("캔들 조회 성공 (%d개, 완성봉=%s)", len(ohlcv), bar_key or "-")

        portfolio = load_state(settings.state_path, settings.paper_cash)
        entry = portfolio.position.entry_price if portfolio.position else None
        result = evaluate(
            strategy,
            ohlcv,
            in_position=portfolio.in_position,
            entry_price=entry,
        )

        usdt: float | None
        if private is not None:
            try:
                usdt = private.available_usdt(symbol)
                if not portfolio.in_position:
                    portfolio.cash = usdt
                logger.info("잔고 조회 성공 | USDT≈%s", fmt_money(usdt))
            except Exception:
                logger.exception("Bitget 잔고 조회 실패")
                usdt = None
        else:
            usdt = portfolio.cash

        risk = load_risk(settings.state_path, integrity_key=settings.risk_integrity_key)
        equity_mark = (usdt or portfolio.cash) + (
            portfolio.position.qty * result.price if portfolio.position else 0.0
        )
        risk = refresh_day(risk, equity_mark)
        risk = check_daily_loss(risk, equity_mark, settings.max_daily_loss_krw)
        save_risk(settings.state_path, risk, integrity_key=settings.risk_integrity_key)

        pos_txt = (
            f"{fmt_qty(portfolio.position.qty)} @ {fmt_money(portfolio.position.entry_price)}"
            if portfolio.position
            else "없음"
        )
        values = {k: round(v, 4) for k, v in result.values.items()}
        status = format_status_block(
            mode=f"{mode}/BITGET",
            strategy=strategy.name,
            market=symbol,
            timeframe=strategy.timeframe,
            price=result.price,
            signal=result.signal.value,
            reason=result.reason,
            krw=usdt,
            base="USDT",
            base_qty=portfolio.position.qty if portfolio.position else 0.0,
            position=pos_txt,
            values=values,
        )
        write_latest_status(settings.log_dir, status)
        write_status_json(
            settings.log_dir,
            {
                "mode": mode,
                "exchange": "bitget",
                "strategy": strategy.name,
                "strategy_file": settings.strategy_path.name,
                "market": symbol,
                "timeframe": strategy.timeframe,
                "price": result.price,
                "signal": result.signal.value,
                "reason": result.reason,
                "usdt": usdt,
                "in_position": portfolio.in_position,
                "position": None
                if not portfolio.position
                else {
                    "qty": portfolio.position.qty,
                    "entry_price": portfolio.position.entry_price,
                    "opened_at": portfolio.position.opened_at,
                },
                "values": values,
                "bar_key": bar_key,
                "risk": {
                    "trading_halted": risk.trading_halted,
                    "halt_reason": risk.halt_reason,
                    "halt_buys_only": risk.halt_buys_only,
                    "consecutive_errors": risk.consecutive_errors,
                },
            },
        )
        logger.info("상태 요약\n%s", status)

        if result.signal == Signal.HOLD:
            save_state(
                settings.state_path,
                portfolio,
                extra={
                    "strategy": strategy.name,
                    "market": symbol,
                    "mode": mode,
                    "exchange": "bitget",
                },
            )
            risk = record_success(risk)
            save_risk(settings.state_path, risk, integrity_key=settings.risk_integrity_key)
            return

        if portfolio.last_signal_bar == bar_key:
            logger.info("이미 처리한 봉(%s) — 건너뜀", bar_key)
            risk = record_success(risk)
            save_risk(settings.state_path, risk, integrity_key=settings.risk_integrity_key)
            return

        is_buy = result.signal == Signal.BUY
        if is_buy and not allow_buy(risk):
            risk = record_success(risk)
            save_risk(settings.state_path, risk, integrity_key=settings.risk_integrity_key)
            return
        if (not is_buy) and not allow_sell(risk):
            risk = record_success(risk)
            save_risk(settings.state_path, risk, integrity_key=settings.risk_integrity_key)
            return

        if settings.paper:
            broker = PaperBroker(settings.fee_rate)
            buy_budget = None
            if is_buy:
                buy_budget = _buy_budget_usdt(portfolio.cash, settings)
                if buy_budget < 5:
                    logger.warning("PAPER Bitget 매수 생략 — 예산 부족 %s USDT", buy_budget)
                    risk = record_success(risk)
                    save_risk(settings.state_path, risk, integrity_key=settings.risk_integrity_key)
                    return
            portfolio = broker.execute(
                portfolio,
                market=symbol,
                signal=result.signal,
                price=result.price,
                reason=result.reason,
                buy_budget=buy_budget,
            )
            trades.info(
                "PAPER BITGET %s | %s | price=%s | reason=%s",
                result.signal.value.upper(),
                symbol,
                result.price,
                result.reason,
            )
            last = portfolio.trades[-1] if portfolio.trades else None
            if is_buy:
                notify.send(
                    format_buy_alert(
                        mode="PAPER/BITGET",
                        strategy=strategy.name,
                        market=symbol,
                        amount_krw=(last.price * last.qty + last.fee) if last else 0.0,
                        price=result.price,
                        reason=result.reason,
                        order_id="paper",
                    )
                )
            else:
                notify.send(
                    format_sell_alert(
                        mode="PAPER/BITGET",
                        strategy=strategy.name,
                        market=symbol,
                        qty=last.qty if last else 0.0,
                        asset=symbol.replace("USDT", ""),
                        price=result.price,
                        reason=result.reason,
                        order_id="paper",
                        entry_price=None,
                        fee=last.fee if last else 0.0,
                    )
                )
            portfolio.last_signal_bar = bar_key
            save_state(
                settings.state_path,
                portfolio,
                extra={
                    "strategy": strategy.name,
                    "market": symbol,
                    "mode": mode,
                    "exchange": "bitget",
                },
            )
            risk = record_success(risk)
            save_risk(settings.state_path, risk, integrity_key=settings.risk_integrity_key)
            return

        assert private is not None
        # LIVE futures: BUY = open long, SELL = close long (one-way)
        if is_buy:
            avail = usdt if usdt is not None else private.available_usdt(symbol)
            notional = _buy_budget_usdt(avail, settings)
            if notional < 5 or result.price <= 0:
                logger.warning("Bitget LIVE 매수 생략 — notional=%s", notional)
                risk = record_success(risk)
                save_risk(settings.state_path, risk, integrity_key=settings.risk_integrity_key)
                return
            size = f"{(notional / result.price):.4f}"
            oid = uuid.uuid4().hex[:32]
            order = private.place_futures_market(
                symbol=symbol,
                size=size,
                side="buy",
                trade_side="open",
                product_type=settings.bitget_product_type,
                margin_coin=settings.bitget_margin_coin,
                margin_mode=settings.bitget_margin_mode,
                client_oid=oid,
            )
            qty = float(size)
            portfolio.cash = private.available_usdt(symbol)
            portfolio.position = Position(
                market=symbol, qty=qty, entry_price=result.price, opened_at=utc_now()
            )
            portfolio.trades.append(
                Trade(
                    ts=utc_now(),
                    side="buy",
                    market=symbol,
                    price=result.price,
                    qty=qty,
                    fee=qty * result.price * settings.fee_rate,
                    reason=result.reason,
                    paper=False,
                )
            )
            trades.info("LIVE BITGET OPEN LONG | %s | size=%s | order=%s", symbol, size, order)
            notify.send(
                format_buy_alert(
                    mode="LIVE/BITGET",
                    strategy=strategy.name,
                    market=symbol,
                    amount_krw=notional,
                    price=result.price,
                    reason=result.reason,
                    order_id=str(order.get("orderId") or oid),
                )
            )
        else:
            if not portfolio.position or portfolio.position.qty <= 0:
                logger.info("Bitget LIVE 청산 생략 — 봇 포지션 없음")
                risk = record_success(risk)
                save_risk(settings.state_path, risk, integrity_key=settings.risk_integrity_key)
                return
            qty = portfolio.position.qty
            size = f"{qty:.4f}"
            oid = uuid.uuid4().hex[:32]
            entry_price = portfolio.position.entry_price
            order = private.place_futures_market(
                symbol=symbol,
                size=size,
                side="sell",
                trade_side="close",
                product_type=settings.bitget_product_type,
                margin_coin=settings.bitget_margin_coin,
                margin_mode=settings.bitget_margin_mode,
                client_oid=oid,
            )
            portfolio.cash = private.available_usdt(symbol)
            portfolio.trades.append(
                Trade(
                    ts=utc_now(),
                    side="sell",
                    market=symbol,
                    price=result.price,
                    qty=qty,
                    fee=qty * result.price * settings.fee_rate,
                    reason=result.reason,
                    paper=False,
                )
            )
            portfolio.position = None
            trades.info("LIVE BITGET CLOSE LONG | %s | size=%s | order=%s", symbol, size, order)
            notify.send(
                format_sell_alert(
                    mode="LIVE/BITGET",
                    strategy=strategy.name,
                    market=symbol,
                    qty=qty,
                    asset=symbol.replace("USDT", ""),
                    price=result.price,
                    reason=result.reason,
                    order_id=str(order.get("orderId") or oid),
                    entry_price=entry_price,
                    fee=qty * result.price * settings.fee_rate,
                )
            )

        portfolio.last_signal_bar = bar_key
        save_state(
            settings.state_path,
            portfolio,
            extra={
                "strategy": strategy.name,
                "market": symbol,
                "mode": mode,
                "exchange": "bitget",
            },
        )
        risk = record_success(risk)
        save_risk(settings.state_path, risk, integrity_key=settings.risk_integrity_key)
        time.sleep(0.2)
    finally:
        public.close()
        if private:
            private.close()
