#!/usr/bin/env python3
"""Weekly CORE observation snapshot (Policy C). Observe only — no map edits."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "reports" / "ops"

MAP = {
    "bull": "regime-bull-trend-4h-v2.json",
    "transition": "regime-bull-trend-4h-v2.json",
    "bear": "krw-btc-1h-ema-adx23-rsi55-sl3-tp45-m5-v6.json",
    "sideways": "regime-sideways-mr-4h-v5.json",
}


def classify_local() -> dict:
    # Prefer remote_regime_switch-style via regime_select if present
    sel = ROOT / "scripts" / "regime_select.py"
    if sel.exists():
        p = subprocess.run(
            [sys.executable, str(sel)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        text = (p.stdout or "") + (p.stderr or "")
        # try JSON line
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("{") and "regime" in line:
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    pass
        # fallback: reports/regime-current.json
    cur = ROOT / "reports" / "regime-current.json"
    if cur.exists():
        return json.loads(cur.read_text(encoding="utf-8"))
    # last resort: engine v2 current
    from scripts.regime_engine_v2 import build_segments, fetch_days

    candles = fetch_days(want=400)
    _segs, current = build_segments(candles)
    return current


def ssh_bot_status() -> str:
    try:
        p = subprocess.run(
            [
                "ssh",
                "-o",
                "BatchMode=yes",
                "-o",
                "ConnectTimeout=12",
                "auto-trade-bot",
                "echo '=== ps ==='; docker ps -a --format '{{.Names}} {{.Status}}' | head -10; "
                "echo '=== STRATEGY ==='; grep -E '^(STRATEGY_PATH|BITGET_STRATEGY)=' ~/auto-trade/.env || true; "
                "echo '=== upbit ==='; docker exec upbit-paper-bot head -18 /app/logs/latest_status.txt 2>/dev/null || echo 'upbit status missing'; "
                "echo '=== bitget ==='; docker ps -a --filter name=bitget --format '{{.Names}} {{.Status}}'",
            ],
            capture_output=True,
            timeout=60,
        )
        def _dec(b: bytes | None) -> str:
            if not b:
                return ""
            return b.decode("utf-8", errors="replace")

        return _dec(p.stdout) + _dec(p.stderr)
    except Exception as e:
        return f"(ssh failed: {type(e).__name__}: {e})"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ssh", action="store_true", help="pull Oracle docker/status via ssh")
    args = ap.parse_args()

    info = classify_local()
    regime = str(info.get("regime") or info.get("label") or "?")
    expected = MAP.get(regime, "?")
    selected = str(info.get("file") or info.get("selected_file") or expected)
    if selected and not selected.endswith(".json"):
        selected = f"{selected}.json" if "/" not in selected else selected

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"weekly-core-obs-{stamp}.md"

    lines = [
        f"# Weekly CORE obs — {stamp}",
        "",
        f"- UTC: `{datetime.now(timezone.utc).isoformat()}`",
        f"- Regime: **{regime}**",
        f"- Expected Policy C file: `{expected}`",
        f"- Classifier file field: `{selected}`",
        f"- Match: **{'YES' if expected in selected or selected.endswith(expected) else 'CHECK'}**",
        "- SCALP LIVE: should be **OFF** (bitget stopped / profile scalp)",
        "- Seed: **Upbit only** (ignore Bitget dust until ≥50만 total)",
        "- Action: observe only — **do not** retune ADX/map",
        "",
        "## Classifier JSON",
        "```json",
        json.dumps(info, indent=2, ensure_ascii=False)[:4000],
        "```",
        "",
    ]
    if args.ssh:
        lines += ["## Oracle snapshot", "```", ssh_bot_status().rstrip(), "```", ""]

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(path)
    print(f"regime={regime} expected={expected}")


if __name__ == "__main__":
    main()
