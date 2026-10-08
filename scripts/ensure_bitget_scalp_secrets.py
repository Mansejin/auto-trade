#!/usr/bin/env python3
"""Ensure Bitget scalp LIVE uses gitignored secrets overlay (not tracked live JSON).

Idempotent. Never prints secret values.
Usage on NAS host:
  python3 scripts/ensure_bitget_scalp_secrets.py /volume1/docker/p3f8c1a2
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _has_creds(ex: dict) -> bool:
    return bool(
        str(ex.get("key") or "").strip()
        and str(ex.get("secret") or "").strip()
        and str(ex.get("password") or "").strip()
    )


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    ud = root / "freqtrade-research" / "user_data"
    live = ud / "config.bitget-scalp-trend-short-live.json"
    secrets = ud / "config.bitget-scalp.secrets.json"
    env_path = root / ".env"

    if not live.is_file():
        print("missing live config", live)
        return 1

    live_data = json.loads(live.read_text(encoding="utf-8"))
    live_ex = dict(live_data.get("exchange") or {})

    sec_data: dict = {"exchange": {"key": "", "secret": "", "password": ""}}
    if secrets.is_file():
        try:
            sec_data = json.loads(secrets.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print("secrets.json invalid JSON — abort")
            return 1
    sec_ex = dict(sec_data.get("exchange") or {})

    moved_from_live = False
    if _has_creds(live_ex) and not _has_creds(sec_ex):
        sec_ex = {
            "key": live_ex["key"],
            "secret": live_ex["secret"],
            "password": live_ex["password"],
        }
        moved_from_live = True

    if not _has_creds(sec_ex) and env_path.is_file():
        env: dict[str, str] = {}
        for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip().strip('"').strip("'")
        cand = {
            "key": env.get("BITGET_API_KEY") or env.get("BITGET_KEY") or "",
            "secret": env.get("BITGET_SECRET_KEY") or env.get("BITGET_SECRET") or "",
            "password": env.get("BITGET_PASSPHRASE") or env.get("BITGET_PASSWORD") or "",
        }
        if _has_creds(cand):
            sec_ex = cand

    if not _has_creds(sec_ex):
        print("no Bitget creds in secrets.json / live / .env — fill secrets.json first")
        return 1

    secrets.parent.mkdir(parents=True, exist_ok=True)
    secrets.write_text(
        json.dumps({"exchange": sec_ex}, indent=2) + "\n",
        encoding="utf-8",
    )
    # Readable by Freqtrade container (ftuser uid 1000). Avoid 0600 as host user.
    try:
        os.chmod(secrets, 0o644)
    except OSError:
        pass

    stripped = False
    if any(str(live_ex.get(k) or "").strip() for k in ("key", "secret", "password")):
        live_ex["key"] = ""
        live_ex["secret"] = ""
        live_ex["password"] = ""
        live_data["exchange"] = live_ex
        live.write_text(json.dumps(live_data, indent=2) + "\n", encoding="utf-8")
        stripped = True

    print(
        "ok secrets=",
        secrets.name,
        "moved_from_live=",
        moved_from_live,
        "stripped_live=",
        stripped,
        "key_len=",
        len(str(sec_ex.get("key") or "")),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
