#!/usr/bin/env python3
"""Upsert Synology Task Scheduler entry for Policy C regime switch (no root sudo needed)."""
from __future__ import annotations

import base64
import shutil
import subprocess
from pathlib import Path

ROOT = Path("/usr/syno/etc/synoschedule.d/root")
NAME = "autotrade-regime-switch-daily"
# After KST daily close (00:00). Matches former Oracle ~15:20 UTC.
SCRIPT = "sh /volume1/docker/p3f8c1a2/scripts/nas_regime_cron.sh"
HOUR = "0"
MINUTE = "20"


def parse_task(text: str) -> dict[str, str]:
    data: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip() or "=" not in line:
            continue
        k, v = line.split("=", 1)
        data[k.strip()] = v
    return data


def dump_task(data: dict[str, str]) -> str:
    order = [
        "id",
        "last work hour",
        "can edit owner",
        "can delete from ui",
        "edit dialog",
        "type",
        "action",
        "systemd slice",
        "monthly week",
        "can edit from ui",
        "week",
        "app name",
        "name",
        "can run app same time",
        "owner",
        "repeat min store config",
        "repeat hour store config",
        "simple edit form",
        "repeat hour",
        "listable",
        "app args",
        "state",
        "can run task same time",
        "start day",
        "cmd",
        "run hour",
        "edit form",
        "app",
        "run min",
        "start month",
        "can edit name",
        "start year",
        "can run from ui",
        "repeat min",
        "cmdArgv",
    ]
    lines = []
    seen = set()
    for k in order:
        if k in data:
            lines.append("%s=%s" % (k, data[k]))
            seen.add(k)
    for k, v in data.items():
        if k not in seen:
            lines.append("%s=%s" % (k, v))
    return "\n".join(lines) + "\n"


def apply_fields(task: dict[str, str], task_id: str) -> dict[str, str]:
    out = dict(task)
    out["id"] = str(task_id)
    out["name"] = NAME
    out["state"] = "enabled"
    out["type"] = "daily"
    out["week"] = "1111111"
    out["run hour"] = HOUR
    out["run min"] = MINUTE
    out["repeat min"] = "0"
    out["repeat hour"] = "0"
    out["owner"] = "0"
    out["action"] = "#common:run#: %s" % SCRIPT
    out["app args"] = (
        '{"notify_enable":false,"notify_if_error":true,"notify_mail":"",'
        '"script":"%s"} ' % SCRIPT
    )
    out["cmd"] = base64.b64encode(SCRIPT.encode("utf-8")).decode("ascii")
    out["cmdArgv"] = ""
    out["app"] = "SYNO.SDS.TaskScheduler.Script"
    out["edit form"] = "SYNO.SDS.TaskScheduler.Script.FormPanel"
    out["edit dialog"] = "SYNO.SDS.TaskScheduler.EditDialog"
    out["app name"] = "#common:command_line#"
    out["listable"] = "1"
    out["can run from ui"] = "1"
    out["can edit from ui"] = "1"
    out["can edit name"] = "1"
    out["can delete from ui"] = "1"
    out["simple edit form"] = "1"
    out["can run task same time"] = "0"
    return out


def main() -> int:
    sample = None
    existing = None
    ids: list[int] = []
    for path in sorted(ROOT.glob("*.task")):
        if path.name.endswith(".bak-ohola"):
            continue
        data = parse_task(path.read_text(encoding="utf-8", errors="replace"))
        try:
            ids.append(int(data.get("id", path.stem.split(".")[0])))
        except ValueError:
            pass
        if data.get("name") == NAME:
            existing = path
        if data.get("app") == "SYNO.SDS.TaskScheduler.Script" and sample is None:
            sample = data
    if sample is None:
        print("no script sample task; abort")
        return 1

    if existing is not None:
        data = parse_task(existing.read_text(encoding="utf-8", errors="replace"))
        task_id = data.get("id", existing.stem.split(".")[0])
        bak = existing.with_suffix(".task.bak-regime")
        if not bak.exists():
            shutil.copy2(existing, bak)
        existing.write_text(dump_task(apply_fields(data, task_id)), encoding="utf-8")
        print("updated", existing.name, "id=%s" % task_id)
    else:
        task_id = str(max(ids) + 1 if ids else 24)
        out = ROOT / ("%s.task" % task_id)
        out.write_text(dump_task(apply_fields(dict(sample), task_id)), encoding="utf-8")
        # DSM often expects a sibling .backup dir
        bak_dir = ROOT / ("%s.backup" % task_id)
        bak_dir.mkdir(exist_ok=True)
        print("created", out.name, "id=%s" % task_id)

    rc = subprocess.call(["/usr/syno/bin/synoschedtask", "--sync"])
    print("synoschedtask --sync rc=%s" % rc)
    # verify
    shown = subprocess.check_output(
        ["/usr/syno/bin/synoschedtask", "--get", "name=%s" % NAME],
        text=True,
        stderr=subprocess.STDOUT,
    )
    print(shown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
