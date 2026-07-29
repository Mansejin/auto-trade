from __future__ import annotations

import logging
import signal
import threading
import time
from datetime import datetime
from typing import Any

from bot.broker import PaperBroker
from bot.config import Settings, load_settings
from bot.display import format_status_block, fmt_money, fmt_qty
from bot.indicators import OHLCV
from bot.logging_setup import setup_logging, trade_logger, write_latest_status, write_status_json
from bot.portfolio import Position, Trade, utc_now
from bot.risk import (
    allow_buy,
    allow_sell,
    check_daily_loss,
    load_risk,
    record_error,
    record_success,
    refresh_day,
    save_risk,
)
from bot.signals import Signal, evaluate
from bot.state_store import load_state, save_state
from bot.strategy_loader import load_strategy
from bot.telegram_commands import HELP, start_command_listener
from bot.telegram_notify import (
    TelegramNotifier,
    format_buy_alert,
    format_sell_alert,
)
from bot.upbit_client import UpbitPrivate, UpbitPublic

logger = logging.getLogger("bot")
_RUNNING = True
_TG_STOP = threading.Event()
_LAST_ERROR_NOTIFY = 0.0
_ERROR_NOTIFY_COOLDOWN = 300.0
_LAST_HALT_NOTIFY = ""


def _handle_stop(signum: int, _frame: Any) -> None:
    global _RUNNING
    logger.info("종료 신호 수신 (%s) — 봇을 멈춥니다.", signum)
    _RUNNING = False
    _TG_STOP.set()


def _closed_bar_key(candles: list[dict[str, Any]]) -> str:
    if len(candles) < 2:
        return ""
    return str(candles[-2].get("candle_date_time_utc") or candles[-2].get("candle_date_time_kst"))


def _notify_error(notify: TelegramNotifier, message: str) -> None:
    global _LAST_ERROR_NOTIFY
    now = time.time()
    if now - _LAST_ERROR_NOTIFY < _ERROR_NOTIFY_COOLDOWN:
        logger.info("오류 텔레그램 알림 쿨다운 중 — 생략")
        return
    _LAST_ERROR_NOTIFY = now
    notify.send(message)


def _notify_halt(notify: TelegramNotifier, reason: str) -> None:
    global _LAST_HALT_NOTIFY
    if reason and reason != _LAST_HALT_NOTIFY:
        _LAST_HALT_NOTIFY = reason
        notify.send(f"거래 중단\n{reason}")


def _buy_budget(krw: float, settings: Settings) -> float:
    budget = krw * (1.0 - settings.fee_rate) * settings.order_fraction
    if settings.max_order_krw > 0:
        budget = min(budget, settings.max_order_krw)
    return float(int(budget))


def _claim_bar(
    settings: Settings,
    portfolio: Any,
    bar_key: str,
    strategy_name: str,
    market: str,
    mode: str,
) -> str | None:
    """Mark bar before order. Returns previous last_signal_bar for unclaim."""
    prev = portfolio.last_signal_bar
    portfolio.last_signal_bar = bar_key
    save_state(
        settings.state_path,
        portfolio,
        extra={
            "strategy": strategy_name,
            "market": market,
            "mode": mode,
            "pending_bar": bar_key,
            "prev_signal_bar": prev,
        },
    )
    return prev


def _unclaim_bar(
    settings: Settings,
    portfolio: Any,
    prev_bar: str | None,
    strategy_name: str,
    market: str,
    mode: str,
) -> None:
    """Roll back claim when order was never accepted by the exchange."""
    portfolio.last_signal_bar = prev_bar
    save_state(
        settings.state_path,
        portfolio,
        extra={
            "strategy": strategy_name,
            "market": market,
            "mode": mode,
            "pending_bar": None,
            "prev_signal_bar": None,
        },
    )
    logger.warning("주문 미접수 — 봉 claim 롤백 (prev=%s)", prev_bar or "-")


def _fill_avg_and_volume(detail: dict[str, Any], order: dict[str, Any], fallback_price: float) -> tuple[float, float]:
    exec_vol = float(detail.get("executed_volume") or order.get("executed_volume") or 0)
    avg = fallback_price
    try:
        trades_raw = detail.get("trades") or []
        if trades_raw:
            num = sum(float(t["price"]) * float(t["volume"]) for t in trades_raw)
            den = sum(float(t["volume"]) for t in trades_raw)
            if den > 0:
                avg = num / den
                if exec_vol <= 0:
                    exec_vol = den
    except Exception:
        pass
    return avg, exec_vol


def run_once(settings: Settings, trades: logging.Logger, notify: TelegramNotifier) -> None:
    if settings.exchange == "bitget":
        from bot.bitget_runner import run_once_bitget  # noqa: PLC0415

        run_once_bitget(settings, trades, notify)
        return

    strategy = load_strategy(settings.strategy_path)
    mode = "PAPER" if settings.paper else "LIVE"
    public = UpbitPublic()
    private: UpbitPrivate | None = None
    base = strategy.market.split("-", 1)[1]

    try:
        if not settings.paper:
            if not settings.live_allowed:
                raise RuntimeError(
                    "LIVE 모드 설정이 부족합니다. "
                    "UPBIT_ACCESS_KEY / UPBIT_SECRET_KEY / "
                    "LIVE_CONFIRM=I_UNDERSTAND_LIVE_TRADING_RISK 가 필요합니다."
                )
            private = UpbitPrivate(settings.upbit_access_key, settings.upbit_secret_key)

        logger.info("캔들 조회 중… market=%s timeframe=%s", strategy.market, strategy.timeframe)
        candles = public.candles(strategy.market, strategy.timeframe, count=200)
        ohlcv = OHLCV.from_upbit_candles(candles)
        bar_key = _closed_bar_key(candles)
        logger.info("캔들 조회 성공 (%d개, 완성봉=%s)", len(candles), bar_key or "-")

        portfolio = load_state(settings.state_path, settings.paper_cash)
        entry = portfolio.position.entry_price if portfolio.position else None
        result = evaluate(
            strategy,
            ohlcv,
            in_position=portfolio.in_position,
            entry_price=entry,
        )

        krw: float | None
        base_qty: float | None
        if private is not None:
            try:
                krw = private.available_balance("KRW")
                base_qty = private.available_balance(base)
                if not portfolio.in_position:
                    portfolio.cash = krw
                logger.info("잔고 조회 성공 | KRW=%s원 | %s=%s", fmt_money(krw), base, fmt_qty(base_qty))
            except Exception:
                logger.exception("잔고 조회 실패 (API 인증/IP/권한 확인 필요)")
                krw, base_qty = None, None
        else:
            krw = portfolio.cash
            base_qty = portfolio.position.qty if portfolio.position else 0.0

        risk = load_risk(settings.state_path, integrity_key=settings.risk_integrity_key)
        if private is not None and krw is not None:
            equity_mark = krw + (
                portfolio.position.qty * result.price if portfolio.position else 0.0
            )
        else:
            equity_mark = portfolio.equity(result.price)
        risk = refresh_day(risk, equity_mark)
        risk = check_daily_loss(risk, equity_mark, settings.max_daily_loss_krw)
        if risk.trading_halted:
            _notify_halt(notify, risk.halt_reason)
        save_risk(settings.state_path, risk, integrity_key=settings.risk_integrity_key)

        if portfolio.position:
            pos_txt = (
                f"{fmt_qty(portfolio.position.qty)}개 "
                f"(평균 {fmt_money(portfolio.position.entry_price)}원)"
            )
        else:
            pos_txt = "없음 (현금만 보유)"

        values = {k: round(v, 4) for k, v in result.values.items()}
        status = format_status_block(
            mode=mode,
            strategy=strategy.name,
            market=strategy.market,
            timeframe=strategy.timeframe,
            price=result.price,
            signal=result.signal.value,
            reason=result.reason,
            krw=krw,
            base=base,
            base_qty=base_qty,
            position=pos_txt,
            values=values,
        )
        write_latest_status(settings.log_dir, status)
        write_status_json(
            settings.log_dir,
            {
                "mode": mode,
                "strategy": strategy.name,
                "strategy_file": settings.strategy_path.name,
                "market": strategy.market,
                "timeframe": strategy.timeframe,
                "price": result.price,
                "signal": result.signal.value,
                "reason": result.reason,
                "krw": krw,
                "base": base,
                "base_qty": base_qty,
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
                "order_fraction": settings.order_fraction,
                "max_order_krw": settings.max_order_krw,
                "risk": {
                    "trading_halted": risk.trading_halted,
                    "halt_reason": risk.halt_reason,
                    "halt_buys_only": risk.halt_buys_only,
                    "consecutive_errors": risk.consecutive_errors,
                    "day_start_equity": risk.day_start_equity,
                    "day_key": risk.day_key,
                },
                "poll_seconds": settings.poll_seconds,
            },
        )
        logger.info("상태 요약\n%s", status)

        if result.signal == Signal.HOLD:
            save_state(
                settings.state_path,
                portfolio,
                extra={"strategy": strategy.name, "market": strategy.market, "mode": mode},
            )
            risk = record_success(risk)
            save_risk(settings.state_path, risk, integrity_key=settings.risk_integrity_key)
            return

        if portfolio.last_signal_bar == bar_key:
            logger.info("이미 처리한 봉(%s) — 중복 주문 건너뜀", bar_key)
            risk = record_success(risk)
            save_risk(settings.state_path, risk, integrity_key=settings.risk_integrity_key)
            return

        is_buy = result.signal == Signal.BUY
        if is_buy and not allow_buy(risk):
            logger.warning("매수 생략 — %s", risk.halt_reason or "거래 중단")
            trades.info("BUY SKIP | halted | %s", risk.halt_reason)
            risk = record_success(risk)
            save_risk(settings.state_path, risk, integrity_key=settings.risk_integrity_key)
            return
        if (not is_buy) and not allow_sell(risk):
            logger.warning("매도 생략 — %s", risk.halt_reason or "거래 중단")
            trades.info("SELL SKIP | halted | %s", risk.halt_reason)
            risk = record_success(risk)
            save_risk(settings.state_path, risk, integrity_key=settings.risk_integrity_key)
            return

        if settings.paper:
            broker = PaperBroker(settings.fee_rate)
            before = portfolio.cash
            buy_budget = None
            if result.signal == Signal.BUY:
                buy_budget = _buy_budget(portfolio.cash, settings)
                if buy_budget < 5000:
                    logger.warning("PAPER 매수 생략 — 예산 부족 %s원", fmt_money(buy_budget))
                    risk = record_success(risk)
                    save_risk(settings.state_path, risk, integrity_key=settings.risk_integrity_key)
                    return
            portfolio = broker.execute(
                portfolio,
                market=strategy.market,
                signal=result.signal,
                price=result.price,
                reason=result.reason,
                buy_budget=buy_budget,
            )
            trades.info(
                "PAPER %s | %s | price=%s | cash %.0f -> %.0f | reason=%s",
                result.signal.value.upper(),
                strategy.market,
                fmt_money(result.price),
                before,
                portfolio.cash,
                result.reason,
            )
            last = portfolio.trades[-1] if portfolio.trades else None
            if result.signal == Signal.BUY:
                notify.send(
                    format_buy_alert(
                        mode="PAPER",
                        strategy=strategy.name,
                        market=strategy.market,
                        amount_krw=(last.price * last.qty + last.fee) if last else before,
                        price=result.price,
                        reason=result.reason,
                        order_id="paper",
                    )
                )
            else:
                entry_px = None
                for t in reversed(portfolio.trades[:-1] if portfolio.trades else []):
                    if t.side == "buy":
                        entry_px = t.price
                        break
                notify.send(
                    format_sell_alert(
                        mode="PAPER",
                        strategy=strategy.name,
                        market=strategy.market,
                        qty=last.qty if last else 0.0,
                        asset=base,
                        price=result.price,
                        reason=result.reason,
                        order_id="paper",
                        entry_price=entry_px,
                        fee=last.fee if last else 0.0,
                    )
                )
            portfolio.last_signal_bar = bar_key
            save_state(
                settings.state_path,
                portfolio,
                extra={"strategy": strategy.name, "market": strategy.market, "mode": mode},
            )
            risk = refresh_day(risk, portfolio.equity(result.price))
            risk = check_daily_loss(risk, portfolio.equity(result.price), settings.max_daily_loss_krw)
            risk = record_success(risk)
            save_risk(settings.state_path, risk, integrity_key=settings.risk_integrity_key)
            if risk.trading_halted:
                _notify_halt(notify, risk.halt_reason)
            return

        assert private is not None

        if result.signal == Signal.BUY:
            if krw is None:
                krw = private.available_balance("KRW")
            amount = _buy_budget(krw, settings)
            if amount < 5000:
                logger.warning(
                    "매수 생략 — 예산 부족 (잔고=%s원, 예산=%s원, 최소 5,000원)",
                    fmt_money(krw),
                    fmt_money(amount),
                )
                trades.info(
                    "LIVE BUY SKIP | %s | krw=%s budget=%s | reason=min_order",
                    strategy.market,
                    fmt_money(krw),
                    fmt_money(amount),
                )
                # Do NOT claim bar — allow retry after deposit
                risk = record_success(risk)
                save_risk(settings.state_path, risk, integrity_key=settings.risk_integrity_key)
                return

            identifier = UpbitPrivate.make_identifier("b")
            bal_before = float(base_qty or 0.0)
            prev_bar = _claim_bar(settings, portfolio, bar_key, strategy.name, strategy.market, mode)
            logger.info(
                "실주문 매수 시도 | 금액=%s원 | 비중=%.0f%% | id=%s",
                fmt_money(amount),
                settings.order_fraction * 100,
                identifier,
            )
            try:
                try:
                    order = private.place_market_buy(strategy.market, amount, identifier=identifier)
                except Exception:
                    logger.exception("매수 주문 실패 — identifier로 조회 시도")
                    try:
                        order = private.get_order(identifier=identifier)
                    except Exception:
                        _unclaim_bar(
                            settings, portfolio, prev_bar, strategy.name, strategy.market, mode
                        )
                        raise

                order_uuid = str(order.get("uuid") or "")
                detail = private.wait_order(uuid_str=order_uuid or None, identifier=identifier)
                avg, exec_vol = _fill_avg_and_volume(detail, order, result.price)
                paid = float(detail.get("paid_fee") or 0)

                time.sleep(0.5)
                bal_after = private.available_balance(base)
                # Prefer executed volume; else balance delta (never whole wallet)
                if exec_vol > 0:
                    qty = exec_vol
                else:
                    qty = max(0.0, bal_after - bal_before)
                if qty <= 0:
                    qty = (amount - amount * settings.fee_rate) / max(avg, 1.0)

                portfolio.cash = private.available_balance("KRW")
                portfolio.position = Position(
                    market=strategy.market,
                    qty=qty,
                    entry_price=avg,
                    opened_at=utc_now(),
                )
                portfolio.trades.append(
                    Trade(
                        ts=utc_now(),
                        side="buy",
                        market=strategy.market,
                        price=avg,
                        qty=qty,
                        fee=paid if paid else amount * settings.fee_rate,
                        reason=result.reason,
                        paper=False,
                    )
                )
                oid = order_uuid or identifier
                trades.info(
                    "LIVE BUY | %s | amount=%s | qty=%s | avg=%s | order=%s | reason=%s",
                    strategy.market,
                    fmt_money(amount),
                    fmt_qty(qty),
                    fmt_money(avg),
                    oid,
                    result.reason,
                )
                logger.info("매수 주문 완료 | uuid=%s | qty=%s", oid, fmt_qty(qty))
                notify.send(
                    format_buy_alert(
                        mode="LIVE",
                        strategy=strategy.name,
                        market=strategy.market,
                        amount_krw=amount,
                        price=avg,
                        reason=result.reason,
                        order_id=str(oid),
                    )
                )
            except Exception:
                # If claim stayed and exception escaped after accepted order, leave claim
                # (anti-duplicate). Unclaim only happened when order was never found.
                raise
        else:
            # Sell only bot-tracked position (never dump whole exchange wallet)
            if not portfolio.position or portfolio.position.qty <= 0:
                logger.info("매도 생략 — 봇 포지션 없음 (거래소 잔고 전량매도 안 함)")
                trades.info("LIVE SELL SKIP | %s | reason=no_bot_position", strategy.market)
                risk = record_success(risk)
                save_risk(settings.state_path, risk, integrity_key=settings.risk_integrity_key)
                return

            exch = private.available_balance(base)
            qty = min(portfolio.position.qty, exch)
            if qty <= 0:
                logger.info("매도 생략 — 거래소 %s 잔고 없음 (state 포지션 정리)", base)
                trades.info("LIVE SELL SKIP | %s | reason=no_exchange_balance", strategy.market)
                portfolio.position = None
                portfolio.last_signal_bar = bar_key
                save_state(
                    settings.state_path,
                    portfolio,
                    extra={"strategy": strategy.name, "market": strategy.market, "mode": mode},
                )
                risk = record_success(risk)
                save_risk(settings.state_path, risk, integrity_key=settings.risk_integrity_key)
                return

            entry_price = portfolio.position.entry_price
            identifier = UpbitPrivate.make_identifier("s")
            prev_bar = _claim_bar(settings, portfolio, bar_key, strategy.name, strategy.market, mode)
            logger.info("실주문 매도 시도 | 수량=%s %s (봇포지션 한도) | id=%s", fmt_qty(qty), base, identifier)
            try:
                order = private.place_market_sell(strategy.market, qty, identifier=identifier)
            except Exception:
                logger.exception("매도 주문 실패 — identifier로 조회 시도")
                try:
                    order = private.get_order(identifier=identifier)
                except Exception:
                    _unclaim_bar(
                        settings, portfolio, prev_bar, strategy.name, strategy.market, mode
                    )
                    raise

            order_uuid = str(order.get("uuid") or "")
            detail = private.wait_order(uuid_str=order_uuid or None, identifier=identifier)
            avg, exec_vol = _fill_avg_and_volume(detail, order, result.price)
            if exec_vol <= 0:
                exec_vol = qty
            paid = float(detail.get("paid_fee") or 0)

            time.sleep(0.5)
            portfolio.cash = private.available_balance("KRW")
            portfolio.trades.append(
                Trade(
                    ts=utc_now(),
                    side="sell",
                    market=strategy.market,
                    price=avg,
                    qty=exec_vol,
                    fee=paid if paid else exec_vol * avg * settings.fee_rate,
                    reason=result.reason,
                    paper=False,
                )
            )
            # Keep residual bot position if partial fill left coins
            remain = max(0.0, portfolio.position.qty - exec_vol)
            portfolio.position = (
                None
                if remain <= 1e-8
                else Position(
                    market=strategy.market,
                    qty=remain,
                    entry_price=entry_price,
                    opened_at=portfolio.position.opened_at,
                )
            )
            oid = order_uuid or identifier
            trades.info(
                "LIVE SELL | %s | qty=%s | avg=%s | order=%s | reason=%s",
                strategy.market,
                fmt_qty(exec_vol),
                fmt_money(avg),
                oid,
                result.reason,
            )
            logger.info("매도 주문 완료 | uuid=%s | qty=%s", oid, fmt_qty(exec_vol))
            notify.send(
                format_sell_alert(
                    mode="LIVE",
                    strategy=strategy.name,
                    market=strategy.market,
                    qty=exec_vol,
                    asset=base,
                    price=avg,
                    reason=result.reason,
                    order_id=str(oid),
                    entry_price=entry_price,
                    fee=paid if paid else exec_vol * avg * settings.fee_rate,
                )
            )

        save_state(
            settings.state_path,
            portfolio,
            extra={
                "strategy": strategy.name,
                "market": strategy.market,
                "mode": mode,
                "pending_bar": None,
                "prev_signal_bar": None,
            },
        )
        live_eq = portfolio.equity(result.price)
        if private is not None:
            try:
                live_eq = private.available_balance("KRW") + (
                    portfolio.position.qty * result.price if portfolio.position else 0.0
                )
            except Exception:
                pass
        risk = refresh_day(risk, live_eq)
        risk = check_daily_loss(risk, live_eq, settings.max_daily_loss_krw)
        risk = record_success(risk)
        save_risk(settings.state_path, risk, integrity_key=settings.risk_integrity_key)
        if risk.trading_halted:
            _notify_halt(notify, risk.halt_reason)
    finally:
        public.close()
        if private:
            private.close()


def main() -> None:
    settings = load_settings()
    setup_logging(settings.log_level, settings.log_dir)
    trades = trade_logger(settings.log_dir)
    notify = TelegramNotifier(settings.telegram_bot_token, settings.telegram_chat_id)
    signal.signal(signal.SIGINT, _handle_stop)
    signal.signal(signal.SIGTERM, _handle_stop)

    mode = "PAPER(모의)" if settings.paper else "LIVE(실주문)"
    logger.info("=" * 48)
    logger.info("자동매매 봇 시작 (exchange=%s)", settings.exchange)
    logger.info("모드       : %s", mode)
    logger.info("거래소     : %s", settings.exchange)
    logger.info("전략 파일  : %s", settings.strategy_path)
    logger.info("폴링 주기  : %s초", settings.poll_seconds)
    logger.info("주문 비중  : %.0f%%", settings.order_fraction * 100)
    logger.info(
        "주문 상한  : %s",
        f"{fmt_money(settings.max_order_krw)}" if settings.max_order_krw > 0 else "없음",
    )
    logger.info(
        "일일 손실  : %s",
        f"{fmt_money(settings.max_daily_loss_krw)}" if settings.max_daily_loss_krw > 0 else "비활성",
    )
    logger.info(
        "연속 오류  : %s",
        f"{settings.max_consecutive_errors}회" if settings.max_consecutive_errors > 0 else "비활성",
    )
    logger.info("로그 폴더  : %s", settings.log_dir)
    logger.info("상태 파일  : %s", settings.state_path)
    logger.info("텔레그램   : %s", "ON" if notify.enabled else "OFF (토큰/채팅ID 미설정)")
    logger.info("이체(반자동): %s", "ON" if settings.transfer_allowed else "OFF")
    if not settings.paper:
        logger.warning("주의: LIVE 모드입니다. 실제 주문이 나갈 수 있습니다.")
        if settings.order_fraction >= 1.0 and settings.max_order_krw <= 0:
            logger.warning(
                "위험: ORDER_FRACTION=100%% 이고 MAX_ORDER_KRW 미설정 — "
                "가용 잔고 전액 진입 가능. MAX_ORDER_KRW 설정을 권장합니다."
            )
    logger.info("=" * 48)

    if notify.enabled:
        start_command_listener(settings, notify, _TG_STOP)
        notify.send(
            f"봇 시작\n거래소: {settings.exchange}\n모드: {mode}\n"
            f"전략: {settings.strategy_path.name}\n"
            f"폴링: {settings.poll_seconds}초\n"
            f"비중: {settings.order_fraction * 100:.0f}%\n\n{HELP}"
        )

    while _RUNNING:
        try:
            run_once(settings, trades, notify)
        except Exception:
            logger.exception("틱 처리 중 오류 — 다음 주기에 재시도합니다.")
            risk = record_error(load_risk(settings.state_path, integrity_key=settings.risk_integrity_key), settings.max_consecutive_errors)
            save_risk(settings.state_path, risk, integrity_key=settings.risk_integrity_key)
            write_latest_status(
                settings.log_dir,
                f"시각      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"상태      : 오류 (bot.log 의 최근 Traceback 확인)\n"
                f"연속오류  : {risk.consecutive_errors}\n",
            )
            write_status_json(
                settings.log_dir,
                {
                    "mode": "LIVE" if not settings.paper else "PAPER",
                    "signal": "error",
                    "reason": "tick failed",
                    "risk": {
                        "trading_halted": risk.trading_halted,
                        "halt_reason": risk.halt_reason,
                        "consecutive_errors": risk.consecutive_errors,
                    },
                    "error": True,
                },
            )
            _notify_error(notify, "봇 오류 발생 — logs/bot.log 를 확인하세요. (5분에 1회)")
            if risk.trading_halted:
                _notify_halt(notify, risk.halt_reason)
        for _ in range(settings.poll_seconds):
            if not _RUNNING:
                break
            time.sleep(1)

    logger.info("봇이 정상 종료되었습니다.")


if __name__ == "__main__":
    main()
