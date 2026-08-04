#!/usr/bin/env python3
import sqlite3

con = sqlite3.connect("/usr/syno/etc/esynoscheduler/esynoscheduler.db")
for name, op, ev in con.execute("SELECT task_name, operation, event FROM task"):
    if any(x in name for x in ("works", "ticket", "saeng", "backup", "docker")):
        print("NAME", name)
        print("OP", op[:500])
        print("EV", ev[:500])
        print("---")
