#!/usr/bin/env python3
"""Patch synoschedule.d/*.task (key=value) after docker folder rename + add backup task."""
import base64
import shutil
from pathlib import Path

ROOT = Path("/usr/syno/etc/synoschedule.d/root")

REPL = {
    "sh /volume1/docker/works-site/api/scripts/nas-dsm-task.sh": "sh /usr/local/bin/ohola-tasks/works-api-auto-pull.sh",
    "/volume1/docker/works-site/api/scripts/nas-dsm-task.sh": "/usr/local/bin/ohola-tasks/works-api-auto-pull.sh",
    "sh /volume1/docker/tools-site/ticket-queue-api/scripts/nas-dsm-task.sh": "sh /usr/local/bin/ohola-tasks/ticket-queue-api-auto-pull.sh",
    "/volume1/docker/tools-site/ticket-queue-api/scripts/nas-dsm-task.sh": "/usr/local/bin/ohola-tasks/ticket-queue-api-auto-pull.sh",
    "/volume1/docker/saenggibu/scripts/nas-scheduled-pull.sh": "/usr/local/bin/ohola-tasks/saenggibu-auto-pull.sh",
    "sh /volume1/docker/saenggibu/scripts/nas-scheduled-pull.sh": "sh /usr/local/bin/ohola-tasks/saenggibu-auto-pull.sh",
    "/volume1/docker/saenggibu/scripts/nas-setup-docker-sudo.sh": "/usr/local/bin/ohola-tasks/saenggibu-docker-sudo.sh",
    "sh /volume1/docker/saenggibu/scripts/nas-setup-docker-sudo.sh": "sh /usr/local/bin/ohola-tasks/saenggibu-docker-sudo.sh",
}


def replace_all(s: str) -> str:
    out = s
    for a, b in REPL.items():
        out = out.replace(a, b)
    return out


def parse_task(text: str):
    data = {}
    for line in text.splitlines():
        if not line.strip() or "=" not in line:
            continue
        k, v = line.split("=", 1)
        data[k.strip()] = v
    return data


def dump_task(data: dict) -> str:
    # preserve a stable order with known keys first
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


def patch_task(data: dict) -> dict:
    out = dict(data)
    for key in ("action", "app args"):
        if key in out:
            out[key] = replace_all(out[key])
    # regenerate cmd base64 from script line in app args if present
    script = None
    args = out.get("app args", "")
    marker = '"script":"'
    if marker in args:
        script = args.split(marker, 1)[1].split('"', 1)[0]
        script = script.replace("\\/", "/")
    if script:
        out["cmd"] = base64.b64encode(script.encode("utf-8")).decode("ascii")
        out["action"] = "#common:run#: %s" % script
    return out


def main():
    ids = []
    has_backup = False
    sample = None
    for path in sorted(ROOT.glob("*.task")):
        if path.name.endswith(".bak-ohola"):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        data = parse_task(text)
        ids.append(int(data.get("id", path.stem.split(".")[0])))
        name = data.get("name", "")
        if "ohola-docker-backup" in name:
            has_backup = True
        if data.get("app") == "SYNO.SDS.TaskScheduler.Script" and sample is None:
            sample = data
        new = patch_task(data)
        new_text = dump_task(new)
        if new_text != dump_task(data):
            bak = path.with_suffix(".task.bak-ohola")
            if not bak.exists():
                shutil.copy2(path, bak)
            path.write_text(new_text, encoding="utf-8")
            print("patched", path.name, name)

    if not has_backup and sample is not None:
        new_id = max(ids) + 1
        task = dict(sample)
        script = "sh /usr/local/bin/ohola-tasks/docker-backup-daily.sh"
        task["id"] = str(new_id)
        task["name"] = "ohola-docker-backup-daily"
        task["state"] = "enabled"
        task["type"] = "daily"
        task["week"] = "1111111"
        task["run hour"] = "3"
        task["run min"] = "20"
        task["repeat min"] = "0"
        task["repeat hour"] = "0"
        task["action"] = "#common:run#: %s" % script
        task["app args"] = (
            '{"notify_enable":false,"notify_if_error":false,"notify_mail":"","script":"%s"} '
            % script
        )
        task["cmd"] = base64.b64encode(script.encode("utf-8")).decode("ascii")
        task["cmdArgv"] = ""
        out = ROOT / ("%d.task" % new_id)
        out.write_text(dump_task(task), encoding="utf-8")
        print("created", out.name)
    elif has_backup:
        print("backup exists")
    else:
        print("no sample; skip create")

    # reload scheduler
    import subprocess

    subprocess.call(["/usr/syno/bin/synoschedtask", "--sync"])
    print("done")


if __name__ == "__main__":
    main()
