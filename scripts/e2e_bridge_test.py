"""E2E bridge test runner — run inside upbit-paper-bot container."""
from __future__ import annotations

import json
import sys
import time

from bot.config import load_settings
from bot import transfer as xfer
from bot import rebalance as rebal
from bot.upbit_client import UpbitPrivate
from bot.bitget_client import BitgetPrivate


def balances(settings):
    up = UpbitPrivate(settings.upbit_access_key, settings.upbit_secret_key)
    bg = BitgetPrivate(
        settings.bitget_api_key,
        settings.bitget_secret_key,
        settings.bitget_passphrase,
        paper_trading=settings.bitget_paper_trading,
    )
    try:
        u = {
            "KRW": up.available_balance("KRW"),
            "TRX": up.available_balance("TRX"),
            "USDT": up.available_balance("USDT"),
        }
        b = {
            "USDT": bg.available_usdt(),
            "TRX": bg.spot_available("TRX"),
        }
    finally:
        up.close()
        bg.close()
    return u, b


def main() -> None:
    step = sys.argv[1] if len(sys.argv) > 1 else "status"
    settings = load_settings()

    u, b = balances(settings)
    print("STEP", step)
    print("UPBIT", json.dumps({k: round(v, 6) for k, v in u.items()}))
    print("BITGET", json.dumps({k: round(v, 6) for k, v in b.items()}))

    if step == "status":
        snap = rebal.snapshot_equity(settings)
        print(rebal.format_snapshot(snap, target=settings.rebalance_target, band=settings.rebalance_band))
        ok, msg = xfer._cooldown_ok(settings)
        print("cooldown", ok, msg)
        print("upbit_whitelist_TRX", (xfer.upbit_whitelist_address(settings, "TRX") or "")[:8])
        print("bitget_whitelist_TRX", (xfer.bitget_whitelist_address(settings, "TRX") or "")[:8])
        return

    if step == "b2u":
        amount = float(sys.argv[2]) if len(sys.argv) > 2 else 5.0
        addr = xfer.upbit_whitelist_address(settings, "TRX")
        if not addr:
            raise RuntimeError("Upbit TRX whitelist missing")
        req = xfer.TransferRequest(
            code="E2ETEST",
            direction="bitget_to_upbit",
            coin="TRX",
            amount=amount,
            chain="TRX",
            created_at=time.time(),
            status="pending",
            detail="e2e_test_b2u",
        )
        detail = xfer._execute(settings, req)
        print("B2U_OK", detail)
        return

    if step == "convert":
        detail = xfer.convert_bitget_trx_to_usdt(settings, min_trx=1.0)
        print("CONVERT_OK", detail)
        return

    if step == "sell_krw":
        target = float(sys.argv[2]) if len(sys.argv) > 2 else u["KRW"] + 1000
        detail = xfer.ensure_upbit_krw(settings, target_krw=target, sell_bridge=True)
        print("SELL_KRW_OK", detail)
        return

    if step == "u2b":
        krw = float(sys.argv[2]) if len(sys.argv) > 2 else 5000.0
        amount, px = xfer.plan_trx_withdraw_amount(top_up_krw=krw, transfer_max=settings.transfer_max_amount)
        detail = xfer.auto_fund_bitget_from_upbit(
            settings,
            amount=amount,
            coin="TRX",
            chain="TRX",
            buy_from_krw=True,
            reason="e2e_test_u2b",
        )
        print("U2B_OK", f"amount={amount} px={px}", detail)
        return

    if step == "propose":
        print(rebal.propose_rebalance(settings, force=True, reason="e2e_test"))
        return

    raise SystemError(f"unknown step {step}")


if __name__ == "__main__":
    main()
