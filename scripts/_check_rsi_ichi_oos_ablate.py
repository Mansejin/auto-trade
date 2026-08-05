"""Check (1) OOS half-year splits (2) long R:R-fixed ablation for RSI+ichi pair.

Uses toolkit long-only files; short_proxy PF = invert(trade pnl_pct).
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.toolkit_bt import run_backtest  # noqa: E402

FEE = 0.0006
OUT = ROOT / "reports" / "rsi-ichi-checks-20260805"
LONG = ROOT / "strategies" / "bitget-btc-5m-rsi-ichi-long-v1.json"
SHORT = ROOT / "strategies" / "bitget-btc-5m-rsi-ichi-short-proxy-v1.json"

OOS = [
    ("h1_trainish", "2025-08-04", "2026-02-03"),
    ("h2_oos", "2026-02-04", "2026-08-04"),
    ("full", "2025-08-04", "2026-08-04"),
]


def parse_perf(csv_path: Path) -> dict[str, float | None]:
    lines = csv_path.read_text(encoding="utf-8").splitlines()
    in_perf = False
    raw: dict[str, str] = {}
    for line in lines:
        if line.startswith("# section: performance"):
            in_perf = True
            continue
        if in_perf and line.startswith("# section:"):
            break
        if not in_perf or line.startswith("metric") or not line.strip():
            continue
        k, v = line.split(",", 1)
        raw[k] = v

    def f(key: str) -> float | None:
        v = raw.get(key)
        if v is None or v.startswith("N/A") or v == "∞":
            return None
        try:
            return float(v)
        except ValueError:
            return None

    return {
        "benchmark_pct": f("benchmark_pct"),
        "total_return_pct": f("total_return_pct"),
        "mdd_pct": f("mdd_pct"),
        "trades": f("trades"),
        "profit_factor_before_fees": f("profit_factor_before_fees"),
        "win_rate_before_fees_pct": f("win_rate_before_fees_pct"),
        "sl_count": f("sl_count"),
        "tp_count": f("tp_count"),
        "sell_count": f("sell_count"),
    }


def parse_trade_pnls(csv_path: Path) -> list[float]:
    lines = csv_path.read_text(encoding="utf-8").splitlines()
    in_tr = False
    header: list[str] | None = None
    pnls: list[float] = []
    for line in lines:
        if line.startswith("# section: trades"):
            in_tr = True
            header = None
            continue
        if in_tr and line.startswith("# section:"):
            break
        if not in_tr or not line.strip():
            continue
        if header is None:
            header = next(csv.reader([line]))
            continue
        row = dict(zip(header, next(csv.reader([line]))))
        pnls.append(float(row["pnl_pct"]))
    return pnls


def pf_from(pnls: list[float]) -> float | None:
    if not pnls:
        return None
    wins = sum(x for x in pnls if x > 0)
    losses = sum(x for x in pnls if x < 0)
    if losses == 0:
        return float("inf") if wins > 0 else None
    return wins / abs(losses)


def eval_long(path: Path, start: str, end: str) -> dict:
    csv_path = run_backtest(path, start, end, fee_rate=FEE)
    perf = parse_perf(csv_path)
    return {
        "side": "long",
        "start": start,
        "end": end,
        "csv": str(csv_path),
        "pf": perf["profit_factor_before_fees"],
        **perf,
    }


def eval_short_proxy(path: Path, start: str, end: str) -> dict:
    csv_path = run_backtest(path, start, end, fee_rate=FEE)
    perf = parse_perf(csv_path)
    pnls = [-x for x in parse_trade_pnls(csv_path)]
    return {
        "side": "short_proxy_inverted",
        "start": start,
        "end": end,
        "csv": str(csv_path),
        "pf": None if not pnls else round(pf_from(pnls) or 0.0, 6),
        "toolkit_long_pf": perf["profit_factor_before_fees"],
        "sum_inverted_pnl_pct": round(sum(pnls), 4),
        **{k: perf[k] for k in perf if k != "profit_factor_before_fees"},
        "trades": perf["trades"],
    }


def make_long_variant(rsi_thr: float, cloud_exit: bool, sl: float, tp: float) -> Path:
    obj = json.loads(LONG.read_text(encoding="utf-8"))
    slug = f"long-ablate-r{rsi_thr}-ce{int(cloud_exit)}-sl{sl}-tp{tp}".replace(".", "p")
    obj["name"] = slug
    obj["stop_loss"] = sl
    obj["take_profit"] = tp
    obj["buy"]["conditions"][0]["right"]["value"] = float(rsi_thr)
    obj["buy"]["conditions"][1]["right"]["value"] = float(rsi_thr)
    if cloud_exit:
        obj["sell"] = {
            "operator": "AND",
            "conditions": [
                {
                    "left": {"type": "field", "field": "close"},
                    "op": "lt",
                    "right": {"type": "indicator", "ref": "ichi.Leading1", "offset": 26},
                },
                {
                    "left": {"type": "field", "field": "close"},
                    "op": "lt",
                    "right": {"type": "indicator", "ref": "ichi.Leading2", "offset": 26},
                },
            ],
        }
    else:
        obj["sell"] = {
            "operator": "AND",
            "conditions": [
                {
                    "left": {"type": "indicator", "ref": "rsi14.rsi"},
                    "op": "gt",
                    "right": {"type": "literal", "value": 99.0},
                }
            ],
        }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{slug}.json"
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    oos_rows: list[dict] = []
    print("=== (1) OOS half-year splits ===", flush=True)
    for label, start, end in OOS:
        print(f"-- {label} {start}..{end}", flush=True)
        long_row = eval_long(LONG, start, end)
        long_row["window"] = label
        oos_rows.append(long_row)
        print(f"  long pf={long_row['pf']} n={long_row['trades']} ret={long_row['total_return_pct']}", flush=True)
        short_row = eval_short_proxy(SHORT, start, end)
        short_row["window"] = label
        oos_rows.append(short_row)
        print(
            f"  short_inv pf={short_row['pf']} n={short_row['trades']} sum_pnl={short_row['sum_inverted_pnl_pct']}",
            flush=True,
        )

    print("=== (3) Long R:R fixed SL0.5/TP1.0 ablation ===", flush=True)
    ablate: list[dict] = []
    for rsi_thr in (22, 25, 28, 30, 35):
        for cloud_exit in (True, False):
            path = make_long_variant(rsi_thr, cloud_exit, 0.5, 1.0)
            for label, start, end in OOS:
                row = eval_long(path, start, end)
                row.update(
                    {
                        "window": label,
                        "rsi_thr": rsi_thr,
                        "cloud_exit": cloud_exit,
                        "sl": 0.5,
                        "tp": 1.0,
                    }
                )
                ablate.append(row)
                print(
                    f"  r{rsi_thr} ce={int(cloud_exit)} {label}: pf={row['pf']} n={row['trades']}",
                    flush=True,
                )

    # also show frozen pair with original R:R already in oos_rows
    payload = {
        "fee_rate": FEE,
        "criteria": "pf>=1.2 and trades>=20 preferred; report facts either way",
        "oos": oos_rows,
        "long_rr_fixed_050_100": ablate,
        "notes": [
            "short pf is inverted long proxy pnl — not Bitget futures engine",
            "h1=2025-08-04..2026-02-03; h2=2026-02-04..2026-08-04",
        ],
    }
    out = OUT / "oos-and-ablate.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out}", flush=True)


if __name__ == "__main__":
    main()
