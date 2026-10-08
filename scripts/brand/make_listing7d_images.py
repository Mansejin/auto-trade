"""@listing7d_kr 채널 이미지: 프로필(640x640, 원형 크롭 안전) + X 헤더(1500x500)."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[2] / "docs/marketing/listing7d/brand"
BOLD = "C:/Windows/Fonts/malgunbd.ttf"
REG = "C:/Windows/Fonts/malgun.ttf"
NAVY, INK, MUTED, ACCENT = "#0B2545", "#FFFFFF", "#8DA9C4", "#F2B134"


def font(path, size):
    return ImageFont.truetype(path, size)


def center_text(d, cx, y, text, f, fill):
    w = d.textlength(text, font=f)
    d.text((cx - w / 2, y), text, font=f, fill=fill)


def day_ticks(d, x0, y, width, active=7, r=9):
    """D+1..D+7 점 7개, 마지막(D+7)만 강조."""
    gap = width / 6
    d.line((x0, y, x0 + width, y), fill=MUTED, width=3)
    for i in range(7):
        x = x0 + i * gap
        rr = r * 1.6 if i == active - 1 else r
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=ACCENT if i == active - 1 else MUTED)


def profile():
    s = 640
    im = Image.new("RGB", (s, s), NAVY)
    d = ImageDraw.Draw(im)
    center_text(d, s / 2, 150, "D+7", font(BOLD, 190), INK)
    day_ticks(d, 175, 420, 290)
    center_text(d, s / 2, 455, "상장 7일 기록", font(BOLD, 40), MUTED)
    im.save(OUT / "profile-640.png")
    return im


def header():
    w, h = 1500, 500
    im = Image.new("RGB", (w, h), NAVY)
    d = ImageDraw.Draw(im)
    d.text((110, 120), "상장공지 7일 기록", font=font(BOLD, 84), fill=INK)
    d.text((114, 240), "업비트 원화 신규상장 → 7일 뒤 결과까지 그대로 기록", font=font(REG, 36), fill=MUTED)
    d.text((114, 300), "매매 지시 없음 · 결과 안 지움", font=font(REG, 30), fill=ACCENT)
    day_ticks(d, 1030, 390, 340, r=11)
    for i, lab in enumerate(["D+1", "D+7"]):
        x = 1030 + i * 340
        center_text(d, x, 420, lab, font(REG, 26), MUTED)
    im.save(OUT / "x-header-1500x500.png")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    im = profile()
    # 원형 크롭 미리보기(텔레그램에서 보이는 모양)
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, *im.size), fill=255)
    prev = Image.new("RGB", im.size, "#FFFFFF")
    prev.paste(im, mask=mask)
    prev.save(OUT / "profile-preview-circle.png")
    header()
    print(sorted(p.name for p in OUT.iterdir()))
