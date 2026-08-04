#!/usr/bin/env python3
"""Merge uploaded local .env with existing NAS tunnel token. Run on NAS only."""
from pathlib import Path


def parse_env(text):
    # Expand accidental literal \n from broken uploads
    if "\\n" in text and text.count("\n") < 5:
        text = text.replace("\\n", "\n").replace("\\r", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if text.startswith("\ufeff"):
        text = text[1:]
    vals = {}
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        vals[k.strip()] = v.strip().strip('"').strip("'")
    return vals


def main():
    root = Path("/volume1/docker/auto-trade")
    broken = (root / ".env").read_text(encoding="utf-8", errors="replace")
    local = (root / ".env.localupload").read_text(encoding="utf-8", errors="replace")
    old = parse_env(broken)
    new = parse_env(local)

    token = old.get("CLOUDFLARE_TUNNEL_TOKEN", "") or new.get("CLOUDFLARE_TUNNEL_TOKEN", "")
    if token:
        new["CLOUDFLARE_TUNNEL_TOKEN"] = token

    defaults = {
        "REBALANCE_ENABLED": "false",
        "REBALANCE_TARGET": "0.5",
        "REBALANCE_BAND": "0.12",
        "REBALANCE_ALERT_COOLDOWN_SEC": "3600",
        "REBALANCE_MIN_MOVE_KRW": "30000",
    }
    for k, v in defaults.items():
        new.setdefault(k, v)

    seen = set()
    local_norm = local.replace("\r\n", "\n").replace("\r", "\n")
    if local_norm.startswith("\ufeff"):
        local_norm = local_norm[1:]
    out_lines = []
    for line in local_norm.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            out_lines.append(line.rstrip("\r"))
            continue
        k = s.split("=", 1)[0].strip()
        if k in seen:
            continue
        seen.add(k)
        out_lines.append("%s=%s" % (k, new[k]))

    for k in list(defaults) + ["CLOUDFLARE_TUNNEL_TOKEN"]:
        if k not in seen and new.get(k):
            out_lines.append("%s=%s" % (k, new[k]))
            seen.add(k)

    dest = root / ".env"
    dest.write_text("\n".join(out_lines).rstrip() + "\n", encoding="utf-8")
    dest.chmod(0o600)

    text = dest.read_text(encoding="utf-8")
    keys = [ln.split("=", 1)[0] for ln in text.splitlines() if ln and not ln.startswith("#") and "=" in ln]
    print(f"lines={text.count(chr(10))+1} keys={len(keys)}")
    for k in (
        "PAPER",
        "LIVE_CONFIRM",
        "UPBIT_ACCESS_KEY",
        "BITGET_API_KEY",
        "CLOUDFLARE_TUNNEL_TOKEN",
        "DASHBOARD_TOKEN",
        "TRANSFER_ENABLED",
    ):
        v = new.get(k, "")
        print(f"{k}={'OK' if v else 'MISSING'} len={len(v)}")


if __name__ == "__main__":
    main()
