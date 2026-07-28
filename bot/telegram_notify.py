from __future__ import annotations

import logging
from datetime import datetime

import httpx

logger = logging.getLogger("bot.telegram")


def _money(v: float) -> str:
    """KRW display — never show decimals."""
    return f"{int(round(v)):,}"


def _qty(v: float) -> str:
    return f"{v:.8f}".rstrip("0").rstrip(".")


def _pnl_line(entry: float | None, exit_price: float, qty: float, fee: float = 0.0) -> list[str]:
    if entry is None or entry <= 0 or qty <= 0:
        return ["손익    (진입가 정보 없음)"]
    proceeds = exit_price * qty
    cost = entry * qty
    pnl = proceeds - cost - fee
    pct = (exit_price - entry) / entry * 100.0
    pnl_i = int(round(pnl))
    pct_i = int(round(pct))
    sign = "+" if pnl_i >= 0 else ""
    result = "이익" if pnl_i >= 0 else "손실"
    return [
        f"진입가  {_money(entry)} 원",
        f"손익    {sign}{pnl_i:,} 원 ({sign}{pct_i}%) · {result}",
    ]


def format_buy_alert(
    *,
    mode: str,
    strategy: str,
    market: str,
    amount_krw: float,
    price: float,
    reason: str,
    order_id: str,
    test: bool = False,
) -> str:
    title = "매수 주문 테스트" if test else "매수 주문 체결"
    badge = "TEST" if test else mode
    return "\n".join(
        [
            "━━━━━━━━━━━━━━━━",
            f"🔴 ▲ {title}",
            "━━━━━━━━━━━━━━━━",
            f"모드    {badge}",
            f"전략    {strategy}",
            f"마켓    {market}",
            f"금액    {_money(amount_krw)} 원",
            f"가격    {_money(price)} 원",
            f"사유    {reason}",
            f"주문번호  {order_id}",
            f"시각    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "━━━━━━━━━━━━━━━━",
        ]
    )


def format_sell_alert(
    *,
    mode: str,
    strategy: str,
    market: str,
    qty: float,
    asset: str,
    price: float,
    reason: str,
    order_id: str,
    entry_price: float | None = None,
    fee: float = 0.0,
    test: bool = False,
) -> str:
    title = "매도 주문 테스트" if test else "매도 주문 체결"
    badge = "TEST" if test else mode
    lines = [
        "━━━━━━━━━━━━━━━━",
        f"🔵 ▼ {title}",
        "━━━━━━━━━━━━━━━━",
        f"모드    {badge}",
        f"전략    {strategy}",
        f"마켓    {market}",
        f"수량    {_qty(qty)} {asset}",
        f"매도가  {_money(price)} 원",
    ]
    lines.extend(_pnl_line(entry_price, price, qty, fee))
    lines.extend(
        [
            f"사유    {reason}",
            f"주문번호  {order_id}",
            f"시각    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "━━━━━━━━━━━━━━━━",
        ]
    )
    return "\n".join(lines)


class TelegramNotifier:
    def __init__(self, token: str, chat_id: str) -> None:
        self.token = token.strip()
        self.chat_id = chat_id.strip()
        self.enabled = bool(self.token and self.chat_id)

    def send(self, text: str) -> bool:
        if not self.enabled:
            return False
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(
                    url,
                    json={
                        "chat_id": self.chat_id,
                        "text": text,
                        "disable_web_page_preview": True,
                    },
                )
                resp.raise_for_status()
            return True
        except Exception:
            logger.exception("텔레그램 전송 실패")
            return False
