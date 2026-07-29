#!/usr/bin/env python3
"""Print CORE vs SCALP sleeve map from config/sleeves.json (read-only)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLEEVES = ROOT / "config" / "sleeves.json"


def _out(s: str) -> None:
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    sys.stdout.buffer.write((s + "\n").encode(encoding, errors="replace"))


def main() -> int:
    if not SLEEVES.exists():
        print(f"missing {SLEEVES}", file=sys.stderr)
        return 1
    data = json.loads(SLEEVES.read_text(encoding="utf-8"))
    w = data.get("weights", {})
    intent = (data.get("intent") or "").replace("\u2014", "-")
    _out(f"dual-sleeve v{data.get('version')}  updated={data.get('updated')}")
    _out(f"weights: CORE {w.get('core_pct')}% / SCALP {w.get('scalp_pct')}%")
    _out(f"intent: {intent}")
    _out("")
    venues = data.get("venues", {})
    for name, v in venues.items():
        _out(f"[{name}] {v.get('venue')}  bot={v.get('bot')}")
        _out(f"         {v.get('role')}")
    _out("")
    for regime, slots in data.get("regimes", {}).items():
        _out(f"## {regime}")
        for sleeve in ("core", "scalp"):
            s = slots.get(sleeve, {})
            strat = s.get("strategy") or "(empty)"
            status = s.get("status", "?")
            _out(f"  {sleeve:5}  {status:22}  {strat}")
            if s.get("notes"):
                note = str(s["notes"]).replace("\u2014", "-")
                _out(f"         {note}")
        _out("")
    _out("ops_rules:")
    for rule in data.get("ops_rules", []):
        _out(f"  - {str(rule).replace(chr(0x2014), '-')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
