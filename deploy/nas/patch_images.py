#!/usr/bin/env python3
"""Insert/replace image: lines next to opaque container_name entries."""
from pathlib import Path


def patch(path, mapping):
    p = Path(path)
    if not p.exists():
        print("missing", path)
        return
    lines = p.read_text(encoding="utf-8").splitlines()
    out = []
    changed = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        matched = None
        for cname, image in mapping.items():
            if stripped == "container_name: %s" % cname:
                matched = image
                break
        if matched is None:
            out.append(line)
            continue
        indent = line[: len(line) - len(line.lstrip())]
        # Replace nearby image: within previous 8 emitted lines
        replaced = False
        for k in range(len(out) - 1, max(-1, len(out) - 9), -1):
            if out[k].strip().startswith("image:"):
                out[k] = "%simage: %s" % (indent, matched)
                replaced = True
                changed = True
                break
        out.append(line)
        if not replaced:
            out.append("%simage: %s" % (indent, matched))
            changed = True
    if changed:
        p.write_text("\n".join(out) + "\n", encoding="utf-8")
        print("patched", path)
    else:
        print("noop", path)


def main():
    patch(
        "/volume1/docker/p8e1b72d/api/docker-compose.yml",
        {
            "p8e1b72d-w1": "p8e1b72d-w1:latest",
            "p8e1b72d-w2": "p8e1b72d-w2:latest",
        },
    )
    patch(
        "/volume1/docker/p6d4a190/ticket-queue-api/docker-compose.yml",
        {"p6d4a190-w1": "p6d4a190-w1:latest"},
    )
    patch(
        "/volume1/docker/p5a0f33c/docker-compose.yml",
        {"p5a0f33c-w1": "p5a0f33c-w1:latest"},
    )
    patch(
        "/volume1/docker/p2c6d9e1/docker-compose.yml",
        {"p2c6d9e1-w1": "p2c6d9e1-w1:latest"},
    )


if __name__ == "__main__":
    main()
