from pathlib import Path

vals = {}
for line in Path("/volume1/docker/p3f8c1a2/.env").read_text(
    encoding="utf-8", errors="replace"
).splitlines():
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    vals[k.strip()] = v.strip().strip('"').strip("'")

for k in ["UPBIT_ACCESS_KEY", "UPBIT_SECRET_KEY", "LIVE_CONFIRM", "PAPER"]:
    v = vals.get(k, "")
    print(k, "len", len(v), "space", " " in v, "prefix", (v[:6] + "...") if len(v) > 6 else v)
