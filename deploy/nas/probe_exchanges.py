#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, "/app")


def main():
    exchange = os.environ.get("EXCHANGE", "upbit")
    if exchange == "bitget":
        from bot.bitget_client import BitgetPrivate

        c = BitgetPrivate(
            os.environ["BITGET_API_KEY"],
            os.environ["BITGET_SECRET_KEY"],
            os.environ["BITGET_PASSPHRASE"],
        )
        try:
            a = c.account_assets()
            print("bitget_ok", type(a).__name__, len(a) if hasattr(a, "__len__") else a)
        except Exception as e:
            r = getattr(e, "response", None)
            print(
                "bitget_err",
                getattr(r, "status_code", None),
                (getattr(r, "text", "") or str(e))[:300],
            )
        return

    from bot.upbit_client import UpbitPrivate

    c = UpbitPrivate(os.environ["UPBIT_ACCESS_KEY"], os.environ["UPBIT_SECRET_KEY"])
    try:
        a = c.accounts()
        print("upbit_ok", len(a))
    except Exception as e:
        r = getattr(e, "response", None)
        print(
            "upbit_err",
            getattr(r, "status_code", None),
            (getattr(r, "text", "") or str(e))[:300],
        )


if __name__ == "__main__":
    main()
