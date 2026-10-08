"""Check the bot's admin rights in the listing alert channel. Run on NAS: python3 deploy/nas/_tg_channel_check.py @listing7d_kr"""
import json
import sys
import urllib.request
from pathlib import Path

env = dict(l.split("=", 1) for l in Path(".env").read_text(encoding="utf-8").splitlines() if "=" in l and not l.startswith("#"))
token = env["TELEGRAM_BOT_TOKEN"].strip().strip('"')
chat = sys.argv[1]


def call(method, **params):
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/{method}", data=json.dumps(params).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=15).read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())


me = call("getMe")["result"]
print("bot:", me["username"])
c = call("getChat", chat_id=chat)
print("chat:", {k: c.get("result", {}).get(k) for k in ("id", "title", "type", "username")} if c.get("ok") else c)
m = call("getChatMember", chat_id=chat, user_id=me["id"])
r = m.get("result", {})
print("member:", r.get("status"), {k: r.get(k) for k in ("can_post_messages", "can_edit_messages", "can_change_info")} if m.get("ok") else m)
