"""Bitget USDT-M futures tick (paper + gated LIVE)."""

from __future__ import annotations

import logging
import time
import uuid

from bot.broker import PaperBroker
from bot.config import Settings
from bot.display import format_status_block, fmt_qty, fmt_quote
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
from bot import transfer as xfer

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
                paper_trading=settings.bitget_paper_trading,
            )

        logger.info(
            "Bitget UTA 캔들 조회… symbol=%s tf=%s category=%s",
            symbol,
            strategy.timeframe,
            settings.bitget_category,
        )
        rows = public.candles(
            symbol,
            strategy.timeframe,
            category=settings.bitget_category,
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
                logger.info("잔고 조회 성공 | USDT≈%s", fmt_quote(usdt, "USDT"))
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

        funding = strategy.funding
        intent = xfer.load_funding_intent(settings) if not settings.paper else None
        force_buy = False
        funding_wait = False
        funding_note = ""
        if intent is not None:
            min_need = float(intent.get("min_trade_usdt") or funding.min_trade_usdt)
            max_wait = float(intent.get("max_wait_sec") or funding.max_wait_sec)
            started = float(intent.get("started_at") or 0.0)
            age = time.time() - started
            fund_coin = str(intent.get("coin") or funding.coin or "TRX").upper()
            do_convert = bool(
                intent.get(
                    "convert_to_usdt",
                    funding.convert_to_usdt if fund_coin == "TRX" else False,
                )
            )
            if fund_coin == "TRX" and do_convert and private is not None:
                try:
                    trx_bal = private.spot_available("TRX")
                    if trx_bal >= 1.0:
                        conv = xfer.convert_bitget_trx_to_usdt(settings)
                        usdt = private.available_usdt(symbol)
                        if not portfolio.in_position:
                            portfolio.cash = usdt or portfolio.cash
                        funding_note = conv
                        logger.info("TRX→USDT 환전: %s | USDT≈%s", conv, usdt)
                except Exception:
                    logger.exception("Bitget TRX→USDT 환전 실패")
                    funding_note = "TRX환전실패(재시도대기)"
            if usdt is not None and usdt >= min_need:
                force_buy = True
                funding_note = (
                    funding_note + " | " if funding_note else ""
                ) + f"입금확인→진입대기(USDT {usdt:.4f})"
                logger.info("자동이체 입금 확인 — deferred futures entry usdt=%.4f", usdt)
            elif age > max_wait:
                expired = intent
                xfer.save_funding_intent(settings, None)
                intent = None
                notify.send(
                    "자동 이체 입금 대기 만료\n"
                    f"보낸 금액: {expired.get('amount')} {expired.get('coin', 'TRX')}\n"
                    "다음 매수 시그널에서 다시 시도합니다."
                )
            else:
                funding_wait = True
                if not funding_note:
                    funding_note = f"입금대기중({int(max_wait - age)}s,{fund_coin})"

        base_asset = symbol.replace("USDT", "") or "BTC"
        pos_txt = (
            f"{fmt_qty(portfolio.position.qty)} {base_asset} @ "
            f"{fmt_quote(portfolio.position.entry_price, 'USDT')}"
            if portfolio.position
            else "없음"
        )
        values = {k: round(v, 4) for k, v in result.values.items()}
        reason_out = result.reason
        if funding_note:
            reason_out = f"{result.reason} | {funding_note}"
        status = format_status_block(
            mode=f"{mode}/BITGET",
            strategy=strategy.name,
            market=symbol,
            timeframe=strategy.timeframe,
            price=result.price,
            signal=result.signal.value if not force_buy else "buy",
            reason=reason_out,
            cash=usdt,
            quote="USDT",
            base=base_asset,
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
                "quote_currency": "USDT",
                "strategy": strategy.name,
                "strategy_file": settings.strategy_path.name,
                "market": symbol,
                "timeframe": strategy.timeframe,
                "price": result.price,
                "signal": result.signal.value,
                "reason": reason_out,
                "usdt": usdt,
                "krw": None,
                "cash": usdt,
                "funding_wait": funding_wait,
                "force_buy": force_buy,
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

        if funding_wait:
            save_state(
                settings.state_path,
                portfolio,
                extra={
                    "strategy": strategy.name,
                    "market": symbol,
                    "mode": mode,
                    "exchange": "bitget",
                    "funding_wait": True,
                },
            )
            risk = record_success(risk)
            save_risk(settings.state_path, risk, integrity_key=settings.risk_integrity_key)
            return

        if result.signal == Signal.HOLD and not force_buy:
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

        if portfolio.last_signal_bar == bar_key and not force_buy:
            logger.info("이미 처리한 봉(%s) — 건너뜀", bar_key)
            risk = record_success(risk)
            save_risk(settings.state_path, risk, integrity_key=settings.risk_integrity_key)
            return

        is_buy = result.signal == Signal.BUY or force_buy
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
                        quote="USDT",
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
                        quote="USDT",
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
            min_need = funding.min_trade_usdt
            if avail < min_need and funding.enabled and not force_buy:
                # Strategy wants a futures entry but UTA margin is short → auto top-up.
                if settings.transfer_max_amount <= 0:
                    notify.send(
                        "선물 진입 시그널인데 Bitget USDT 부족합니다.\n"
                        f"가용 {avail:.4f} < 최소 {min_need}.\n"
                        "자동 이체를 쓰려면 TRANSFER_MAX_AMOUNT>0 과 "
                        "TRANSFER_ENABLED/CONFIRM, 화이트리스트를 설정하세요."
                    )
                    risk = record_success(risk)
                    save_risk(settings.state_path, risk, integrity_key=settings.risk_integrity_key)
                    return
                coin_u = (funding.coin or "TRX").upper()
                chain_u = "TRX" if coin_u == "TRX" else funding.chain
                try:
                    if coin_u == "TRX":
                        top_up, trx_px = xfer.plan_trx_withdraw_amount(
                            top_up_krw=funding.top_up_krw,
                            transfer_max=settings.transfer_max_amount,
                        )
                        detail = xfer.auto_fund_bitget_from_upbit(
                            settings,
                            amount=float(f"{top_up:.6f}"),
                            coin="TRX",
                            chain="TRX",
                            buy_from_krw=funding.buy_from_krw,
                            reason=f"futures_entry_signal:{result.reason}",
                        )
                        bridge_line = (
                            f"Upbit KRW→TRX→Bitget (예산 {funding.top_up_krw:.0f}원, "
                            f"~{top_up} TRX @ {trx_px:.2f}) → Bitget TRX→USDT"
                        )
                    else:
                        top_up = min(funding.top_up_usdt, settings.transfer_max_amount)
                        top_up = max(top_up, min(min_need, settings.transfer_max_amount))
                        detail = xfer.auto_fund_bitget_from_upbit(
                            settings,
                            amount=float(f"{top_up:.4f}"),
                            coin=coin_u,
                            chain=chain_u,
                            buy_from_krw=funding.buy_from_krw,
                            reason=f"futures_entry_signal:{result.reason}",
                        )
                        bridge_line = f"Upbit → Bitget {top_up} {coin_u} ({chain_u})"
                    xfer.save_funding_intent(
                        settings,
                        {
                            "status": "awaiting_deposit",
                            "started_at": time.time(),
                            "amount": top_up,
                            "top_up_krw": funding.top_up_krw if coin_u == "TRX" else None,
                            "coin": coin_u,
                            "chain": chain_u,
                            "convert_to_usdt": funding.convert_to_usdt if coin_u == "TRX" else False,
                            "min_trade_usdt": min_need,
                            "max_wait_sec": funding.max_wait_sec,
                            "bar_key": bar_key,
                            "reason": result.reason,
                        },
                    )
                    notify.send(
                        "======= 자동 이체 실행 =======\n"
                        f"사유: 선물 진입 시그널 + Bitget USDT 부족 ({avail:.4f} < {min_need})\n"
                        f"{bridge_line}\n"
                        f"{detail}\n"
                        "입금·환전 확인 후 다음 틱에서 자동 진입합니다.\n"
                        "==============================="
                    )
                except Exception as e:
                    logger.exception("자동 이체 실패")
                    notify.send(f"자동 이체 실패: {type(e).__name__}: {e}")
                risk = record_success(risk)
                save_risk(settings.state_path, risk, integrity_key=settings.risk_integrity_key)
                return

            notional = _buy_budget_usdt(avail, settings)
            if force_buy and notional < min_need and avail >= min_need:
                notional = min(avail, settings.max_order_krw) if settings.max_order_krw > 0 else avail
            if notional < min(5.0, min_need) or result.price <= 0:
                logger.warning("Bitget LIVE 매수 생략 — notional=%s avail=%s", notional, avail)
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
                product_type=settings.bitget_category,
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
                    reason=result.reason if not force_buy else f"{result.reason}|funded_entry",
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
                    reason=result.reason if not force_buy else f"{result.reason}|funded_entry",
                    order_id=str(order.get("orderId") or oid),
                    quote="USDT",
                )
            )
            if force_buy or intent is not None:
                xfer.save_funding_intent(settings, None)
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
                product_type=settings.bitget_category,
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
                    quote="USDT",
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
