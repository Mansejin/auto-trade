"""Long-only extension grid after primary RSI+ichi search missed PF>=1.2 on long."""
from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

# Import after path setup via runpy-style
from _search_rsi_ichi_pf12 import Spec, build_json, eval_spec  # noqa: E402

OUT = ROOT / "reports" / "rsi-ichi-pf-search-20260805"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    extra: list[Spec] = []
    for thr, (sl, tp), cloud, cloud_exit in product(
        (22, 24, 26, 28, 30),
        (
            (0.25, 0.8),
            (0.3, 1.0),
            (0.3, 1.2),
            (0.4, 1.2),
            (0.4, 1.6),
            (0.5, 2.0),
            (0.8, 2.4),
            (1.0, 3.0),
        ),
        (False, True),
        (True, False),
    ):
        extra.append(Spec("long", thr, sl, tp, cloud, cloud_exit))
    print(f"long_extra={len(extra)}", flush=True)
    hits: list[dict] = []
    rows: list[dict] = []
    with ProcessPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(eval_spec, s): s for s in extra}
        for fut in as_completed(futs):
            s = futs[fut]
            try:
                row = fut.result()
            except Exception as e:  # noqa: BLE001
                row = {
                    "slug": s.slug,
                    "error": str(e)[-200:],
                    "hit": False,
                    "pf": None,
                    "trades": 0,
                }
            rows.append(row)
            print(
                f"{row.get('slug')} n={row.get('trades')} pf={row.get('pf')} hit={row.get('hit')}",
                flush=True,
            )
            if row.get("hit"):
                hits.append(row)
                obj = build_json(s)
                text = json.dumps(obj, ensure_ascii=False, indent=2)
                (ROOT / "strategies" / f"{s.slug}.json").write_text(text, encoding="utf-8")
                (OUT / f"{s.slug}.json").write_text(text, encoding="utf-8")
    rows2 = sorted(
        [r for r in rows if r.get("pf") is not None],
        key=lambda r: (r.get("pf") or 0),
        reverse=True,
    )
    payload = {"hits": hits, "top15": rows2[:15], "n": len(rows)}
    (OUT / "long-extra-summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"LONG_HITS={len(hits)}", flush=True)
    if rows2:
        print(f"BEST={rows2[0].get('slug')} pf={rows2[0].get('pf')} n={rows2[0].get('trades')}", flush=True)


if __name__ == "__main__":
    main()
