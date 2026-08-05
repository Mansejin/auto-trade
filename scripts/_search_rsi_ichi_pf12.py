"""Grid-search 5m RSI+Ichimoku long / Bitget-short-proxy until PF>=1.2.

Upbit toolkit = long-only / kr. Short candidates are entry-timing proxies
(buy on overbought+below-cloud); short_pf is computed by inverting trade pnl_pct.
"""
from __future__ import annotations

import csv
import io
import json
import sys
import tempfile
from dataclasses import asdict, dataclass
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.toolkit_bt import run_backtest  # noqa: E402

START, END = "2025-08-04", "2026-08-04"  # ~1y of 5m ≈ 105k bars
FEE = 0.0006  # Bitget taker approx one side; toolkit applies round-trip per trade fill model
OUT = ROOT / "reports" / "rsi-ichi-pf-search-20260805"
MIN_TRADES = 20
TARGET_PF = 1.2


@dataclass(frozen=True)
class Spec:
    side: str  # long | short_proxy
    rsi_thr: int
    sl: float
    tp: float
    cloud: bool
    cloud_exit: bool

    @property
    def slug(self) -> str:
        c = "c1" if self.cloud else "c0"
        e = "e1" if self.cloud_exit else "e0"
        return f"rsi-ichi-5m-{self.side}-r{self.rsi_thr}-sl{self.sl}-tp{self.tp}-{c}-{e}"


def build_json(spec: Spec) -> dict:
    ichi = {
        "type": "ichimoku_cloud",
        "ref": "ichi",
        "params": {"conversion": 9, "base": 26, "leading_span2": 52},
    }
    rsi = {
        "type": "rsi",
        "ref": "rsi14",
        "params": {"period": 14, "signal_period": 9, "signal_type": "EMA"},
    }
    base = {
        "name": spec.slug,
        "market": "KRW-BTC",
        "exchange": "kr",
        "timeframe": "5m",
        "stop_loss": spec.sl,
        "take_profit": spec.tp,
        "indicators": [rsi, ichi],
    }
    if spec.side == "long":
        buy_conds = [
            {
                "left": {"type": "indicator", "ref": "rsi14.rsi", "offset": 1},
                "op": "lt",
                "right": {"type": "literal", "value": float(spec.rsi_thr)},
            },
            {
                "left": {"type": "indicator", "ref": "rsi14.rsi"},
                "op": "gt",
                "right": {"type": "literal", "value": float(spec.rsi_thr)},
            },
        ]
        if spec.cloud:
            buy_conds += [
                {
                    "left": {"type": "field", "field": "close"},
                    "op": "gt",
                    "right": {"type": "indicator", "ref": "ichi.Leading1", "offset": 26},
                },
                {
                    "left": {"type": "field", "field": "close"},
                    "op": "gt",
                    "right": {"type": "indicator", "ref": "ichi.Leading2", "offset": 26},
                },
            ]
        if spec.cloud_exit:
            sell = {
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
            # unreachable sell → SL/TP drive exits
            sell = {
                "operator": "AND",
                "conditions": [
                    {
                        "left": {"type": "indicator", "ref": "rsi14.rsi"},
                        "op": "gt",
                        "right": {"type": "literal", "value": 99.0},
                    }
                ],
            }
    else:
        # short_proxy: buy when RSI fades from overbought + optionally below cloud
        thr = spec.rsi_thr
        buy_conds = [
            {
                "left": {"type": "indicator", "ref": "rsi14.rsi", "offset": 1},
                "op": "gt",
                "right": {"type": "literal", "value": float(thr)},
            },
            {
                "left": {"type": "indicator", "ref": "rsi14.rsi"},
                "op": "lt",
                "right": {"type": "literal", "value": float(thr)},
            },
        ]
        if spec.cloud:
            buy_conds += [
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
            ]
        if spec.cloud_exit:
            # cover when reclaiming cloud (mirror)
            sell = {
                "operator": "AND",
                "conditions": [
                    {
                        "left": {"type": "field", "field": "close"},
                        "op": "gt",
                        "right": {"type": "indicator", "ref": "ichi.Leading1", "offset": 26},
                    },
                    {
                        "left": {"type": "field", "field": "close"},
                        "op": "gt",
                        "right": {"type": "indicator", "ref": "ichi.Leading2", "offset": 26},
                    },
                ],
            }
        else:
            sell = {
                "operator": "AND",
                "conditions": [
                    {
                        "left": {"type": "indicator", "ref": "rsi14.rsi"},
                        "op": "lt",
                        "right": {"type": "literal", "value": 1.0},
                    }
                ],
            }

    base["buy"] = {"operator": "AND", "conditions": buy_conds}
    base["sell"] = sell
    return base


def parse_trades(csv_path: Path) -> list[dict]:
    lines = csv_path.read_text(encoding="utf-8").splitlines()
    in_tr = False
    header: list[str] | None = None
    rows: list[dict] = []
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
        vals = next(csv.reader([line]))
        rows.append(dict(zip(header, vals)))
    return rows


def parse_toolkit_pf(csv_path: Path) -> tuple[float | None, int]:
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
    trades = int(float(raw["trades"])) if raw.get("trades") not in (None, "N/A") else 0
    pf_s = raw.get("profit_factor_before_fees")
    pf = None if pf_s in (None, "N/A", "∞") else float(pf_s)
    return pf, trades


def pf_from_pnls(pnls: list[float]) -> float | None:
    if not pnls:
        return None
    wins = sum(x for x in pnls if x > 0)
    losses = sum(x for x in pnls if x < 0)
    if losses == 0:
        return float("inf") if wins > 0 else None
    return wins / abs(losses)


def eval_spec(spec: Spec) -> dict:
    obj = build_json(spec)
    with tempfile.TemporaryDirectory(prefix="rsiichi_") as td:
        path = Path(td) / f"{spec.slug}.json"
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
        # persist candidate copy under reports for winners only later
        csv_path = run_backtest(path, START, END, fee_rate=FEE, quiet=True)
    toolkit_pf, n = parse_toolkit_pf(csv_path)
    trades = parse_trades(csv_path)
    long_pnls = [float(t["pnl_pct"]) for t in trades]
    if spec.side == "long":
        pf = toolkit_pf
        use_pnls = long_pnls
    else:
        # inverted PnL = Bitget short side approximation
        use_pnls = [-x for x in long_pnls]
        pf = pf_from_pnls(use_pnls)
    return {
        **asdict(spec),
        "slug": spec.slug,
        "trades": n,
        "pf": None if pf is None else round(pf, 6),
        "toolkit_pf_long": toolkit_pf,
        "sum_pnl_pct": round(sum(use_pnls), 4) if use_pnls else 0.0,
        "csv": str(csv_path),
        "hit": bool(pf is not None and n >= MIN_TRADES and pf >= TARGET_PF),
    }


def grid() -> list[Spec]:
    specs: list[Spec] = []
    long_thr = (25, 28, 30, 32, 35)
    short_thr = (75, 72, 70, 68, 65)
    sltps = ((0.3, 0.8), (0.4, 0.8), (0.5, 1.0), (0.5, 1.5), (0.8, 1.6), (1.0, 2.0))
    for thr, (sl, tp), cloud, cloud_exit in product(long_thr, sltps, (True, False), (True, False)):
        specs.append(Spec("long", thr, sl, tp, cloud, cloud_exit))
    for thr, (sl, tp), cloud, cloud_exit in product(short_thr, sltps, (True, False), (True, False)):
        specs.append(Spec("short_proxy", thr, sl, tp, cloud, cloud_exit))
    return specs


def main() -> None:
    from concurrent.futures import ProcessPoolExecutor, as_completed

    OUT.mkdir(parents=True, exist_ok=True)
    specs = grid()
    print(
        f"grid_size={len(specs)} window={START}..{END} target_pf={TARGET_PF} min_trades={MIN_TRADES}",
        flush=True,
    )
    results: list[dict] = []
    hits: list[dict] = []

    def _handle(row: dict, spec: Spec | None = None) -> None:
        results.append(row)
        pf = row.get("pf")
        print(
            f"[{len(results)}/{len(specs)}] {row.get('slug')} trades={row.get('trades')} pf={pf} hit={row.get('hit')}",
            flush=True,
        )
        if not row.get("hit"):
            return
        hits.append(row)
        s = spec or Spec(row["side"], row["rsi_thr"], row["sl"], row["tp"], row["cloud"], row["cloud_exit"])
        obj = build_json(s)
        text = json.dumps(obj, ensure_ascii=False, indent=2)
        (OUT / f"{s.slug}.json").write_text(text, encoding="utf-8")
        (ROOT / "strategies" / f"{s.slug}.json").write_text(text, encoding="utf-8")
        print(f"*** HIT {s.slug} pf={pf} trades={row['trades']}", flush=True)

    # Phase 1: parallel primary grid
    with ProcessPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(eval_spec, s): s for s in specs}
        for fut in as_completed(futs):
            spec = futs[fut]
            try:
                row = fut.result()
            except Exception as e:  # noqa: BLE001
                row = {
                    **asdict(spec),
                    "slug": spec.slug,
                    "error": str(e)[-300:],
                    "hit": False,
                    "pf": None,
                    "trades": 0,
                }
            _handle(row, spec)

    if not (any(h["side"] == "long" for h in hits) and any(h["side"] == "short_proxy" for h in hits)):
        print("missing side hit - level-entry extension", flush=True)
        extra: list[Spec] = []
        for side, thrs in (("long", (20, 25, 30)), ("short_proxy", (80, 75, 70))):
            for thr, (sl, tp) in product(thrs, ((0.3, 0.9), (0.4, 1.2), (0.6, 1.8))):
                extra.append(Spec(side, thr, sl, tp, True, False))
                extra.append(Spec(side, thr, sl, tp, False, False))
        # skip already evaluated
        seen = {r.get("slug") for r in results}
        extra = [s for s in extra if s.slug not in seen]
        with ProcessPoolExecutor(max_workers=4) as ex:
            futs = {ex.submit(eval_spec, s): s for s in extra}
            for fut in as_completed(futs):
                spec = futs[fut]
                try:
                    row = fut.result()
                except Exception as e:  # noqa: BLE001
                    row = {
                        **asdict(spec),
                        "slug": spec.slug,
                        "error": str(e)[-300:],
                        "hit": False,
                        "pf": None,
                        "trades": 0,
                    }
                _handle(row, spec)

    results_sorted = sorted(
        [r for r in results if r.get("pf") is not None],
        key=lambda r: (r.get("hit") is True, r.get("pf") or 0, r.get("trades") or 0),
        reverse=True,
    )
    payload = {
        "start": START,
        "end": END,
        "fee_rate": FEE,
        "target_pf": TARGET_PF,
        "min_trades": MIN_TRADES,
        "note": (
            "short_proxy pf inverts toolkit long pnl_pct; not a true Bitget futures engine. "
            "exchange bitget not supported by upbit-strategy-toolkit validate."
        ),
        "hits": hits,
        "top20": results_sorted[:20],
        "n_eval": len(results),
    }
    out = OUT / "search-summary.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out} hits={len(hits)}", flush=True)
    for h in hits:
        print(f"HIT {h['side']} {h['slug']} pf={h['pf']} n={h['trades']}", flush=True)
    if not hits and results_sorted:
        b = results_sorted[0]
        print(f"best_nonhit {b.get('slug')} pf={b.get('pf')} n={b.get('trades')}", flush=True)


if __name__ == "__main__":
    main()
