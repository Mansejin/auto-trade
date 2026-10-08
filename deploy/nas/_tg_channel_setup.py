"""One-time channel setup: description + pinned post. Run on NAS from deploy root:
python3 deploy/nas/_tg_channel_setup.py @listing7d_kr
Idempotent via logs/listing-channel-setup.json (won't post the pinned message twice)."""
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

env = dict(l.split("=", 1) for l in Path(".env").read_text(encoding="utf-8").splitlines() if "=" in l and not l.startswith("#"))
token = env["TELEGRAM_BOT_TOKEN"].strip().strip('"')
chat = sys.argv[1]
mark = Path("logs/listing-channel-setup.json")
BIO = ("업비트 원화 신규상장 공지 15분 뒤, 그 코인의 해외 무기한 현황과 과거 상장 133건의 7일 가격 분포를 보냅니다. "
       "7일 뒤 실제 결과도 남깁니다. 매매 지시 없음. 투자 권유 아님, 원금 손실 가능.")


def call(method, **params):
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/{method}", data=json.dumps(params).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=15).read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())


assert len(BIO) <= 255, len(BIO)
print("description:", call("setChatDescription", chat_id=chat, description=BIO))
if mark.exists():
    print("pinned already posted:", mark.read_text(encoding="utf-8"))
    sys.exit()
text = Path("docs/sales/upbit-listing-alert/pinned.txt").read_text(encoding="utf-8")
sent = call("sendMessage", chat_id=chat, text=text, disable_web_page_preview=True)
print("send:", sent.get("ok"), sent.get("description", ""))
if sent.get("ok"):
    mid = sent["result"]["message_id"]
    print("pin:", call("pinChatMessage", chat_id=chat, message_id=mid, disable_notification=True))
    mark.write_text(json.dumps({"chat": chat, "message_id": mid, "date": sent["result"]["date"]}), encoding="utf-8")
