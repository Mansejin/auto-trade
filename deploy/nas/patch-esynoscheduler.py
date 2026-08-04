#!/usr/bin/env python3
"""Patch Synology Task Scheduler DB paths + upsert daily docker backup task."""
import json
import sqlite3
from pathlib import Path

DB = Path("/usr/syno/etc/esynoscheduler/esynoscheduler.db")

REPLACEMENTS = {
    "/volume1/docker/works-site/api/scripts/nas-dsm-task.sh": "/usr/local/bin/ohola-tasks/works-api-auto-pull.sh",
    "/volume1/docker/tools-site/ticket-queue-api/scripts/nas-dsm-task.sh": "/usr/local/bin/ohola-tasks/ticket-queue-api-auto-pull.sh",
    "/volume1/docker/saenggibu/scripts/nas-scheduled-pull.sh": "/usr/local/bin/ohola-tasks/saenggibu-auto-pull.sh",
    "/volume1/docker/saenggibu/scripts/nas-setup-docker-sudo.sh": "/usr/local/bin/ohola-tasks/saenggibu-docker-sudo.sh",
}

BACKUP_NAME = "ohola-docker-backup-daily"
BACKUP_OP = {
    "type": "script",
    "script": "sh /usr/local/bin/ohola-tasks/docker-backup-daily.sh",
}


def patch_text(s: str) -> str:
    out = s
    for a, b in REPLACEMENTS.items():
        out = out.replace(a, b)
    return out


def main() -> None:
    con = sqlite3.connect(str(DB))
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    rows = cur.execute("SELECT task_name, operation, event, enable FROM task").fetchall()
    changed = 0
    for row in rows:
        op = row["operation"] or ""
        new_op = patch_text(op)
        if new_op != op:
            cur.execute(
                "UPDATE task SET operation=? WHERE task_name=?",
                (new_op, row["task_name"]),
            )
            changed += 1
            print("patched", row["task_name"])
        else:
            # show if still contains old docker paths
            if "/volume1/docker/" in op and "p3f8c1a2" not in op and "ohola-tasks" not in op:
                print("still-old?", row["task_name"], op[:120])

    names = {r["task_name"] for r in rows}
    if BACKUP_NAME not in names:
        # clone event schedule from a simple daily task if possible
        sample = cur.execute(
            "SELECT event FROM task WHERE event LIKE '%daily%' OR event LIKE '%time%' LIMIT 1"
        ).fetchone()
        # Minimal daily 03:20 event JSON used by DSM (best-effort)
        event = {
            "schedule": {
                "date_type": 0,
                "week_days": "0,1,2,3,4,5,6",
                "hour": 3,
                "minute": 20,
                "repeat_hour": 0,
                "repeat_min": 0,
                "last_work_hour": 0,
            }
        }
        if sample and sample["event"]:
            try:
                ev = json.loads(sample["event"])
                # keep structure, force 03:20 daily if keys exist
                if isinstance(ev, dict):
                    event = ev
                    sch = event.get("schedule") or event
                    if isinstance(sch, dict):
                        for k, v in (("hour", 3), ("minute", 20)):
                            if k in sch:
                                sch[k] = v
            except Exception:
                pass
        cur.execute(
            """
            INSERT INTO task(task_name, description, event, enable, owner, operation, operation_type, status)
            VALUES(?,?,?,?,?,?,?,?)
            """,
            (
                BACKUP_NAME,
                "Daily /volume1/docker backup (local + optional rclone)",
                json.dumps(event, ensure_ascii=False),
                1,
                0,  # root
                json.dumps(BACKUP_OP, ensure_ascii=False),
                "script",
                "{}",
            ),
        )
        print("inserted", BACKUP_NAME)
    else:
        print("backup task exists")

    con.commit()
    con.close()
    print("changed_rows", changed)


if __name__ == "__main__":
    main()
