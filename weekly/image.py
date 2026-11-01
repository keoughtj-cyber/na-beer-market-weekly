"""Compose the weekly social image (1080x1350, 4:5) from product photos."""
import io
import os
import urllib.request

from PIL import Image, ImageDraw, ImageFont, ImageOps

from .http import USER_AGENT

W, H = 1080, 1350
RED = (161, 20, 15)
CREAM = (247, 241, 230)
INK = (40, 30, 25)
HERE = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(HERE, "..", "assets", "logo-red.png")
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def _font(size):
    for f in FONT_CANDIDATES:
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default(size)


def _fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as r:
        return Image.open(io.BytesIO(r.read())).convert("RGB")


def _wrap(draw, text, font, width):
    lines, line = [], ""
    for word in text.split():
        test = f"{line} {word}".strip()
        if draw.textlength(test, font=font) <= width:
            line = test
        else:
            lines.append(line)
            line = word
    return lines + [line] if line else lines


def compose(headline, image_urls, out_path, footer="Shop at nabeermarket.com",
            fetch=_fetch):
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)

    # Headline band
    band_h = 250
    d.rectangle([0, 0, W, band_h], fill=RED)
    size = 76
    while size > 40:
        font = _font(size)
        lines = _wrap(d, headline, font, W - 120)
        if len(lines) <= 2:
            break
        size -= 6
    y = (band_h - len(lines) * (size + 12)) // 2
    for ln in lines:
        d.text(((W - d.textlength(ln, font=font)) // 2, y), ln, font=font, fill="white")
        y += size + 12

    # Product grid: 3 on top, the rest below, centred
    urls = image_urls[:6]
    rows = [urls[:3], urls[3:]] if len(urls) > 3 else [urls]
    top, bottom, gap = band_h + 40, H - 170 - 40, 24
    row_h = (bottom - top - gap * (len(rows) - 1)) // len(rows)
    cell_w = (W - 80 - gap * 2) // 3
    for r, row in enumerate(rows):
        row_w = len(row) * cell_w + (len(row) - 1) * gap
        x = (W - row_w) // 2
        ry = top + r * (row_h + gap)
        for url in row:
            mask = Image.new("L", (cell_w, row_h), 0)
            ImageDraw.Draw(mask).rounded_rectangle([0, 0, cell_w - 1, row_h - 1], radius=22, fill=255)
            try:
                photo = ImageOps.fit(fetch(url), (cell_w, row_h), centering=(0.5, 0.5))
            except Exception as e:  # a missing photo shouldn't sink the week
                print(f"warning: could not load {url}: {e}")
                photo = Image.new("RGB", (cell_w, row_h), "white")
            img.paste(photo, (x, ry), mask)
            x += cell_w + gap

    # Footer: white strip with logo + shop line
    d.rectangle([0, H - 170, W, H], fill="white")
    try:
        logo = Image.open(LOGO).convert("RGBA")
        logo = ImageOps.contain(logo, (300, 110))
        img.paste(logo, (60, H - 140), logo)
        fx = 60 + logo.width + 30
    except OSError:
        fx = 60
    ff = _font(34)
    d.text((fx, H - 105), footer, font=ff, fill=INK)

    img.save(out_path, "PNG", optimize=True)
    return out_path
