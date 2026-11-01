"""Compose the weekly social image (1080x1350, 4:5) from product photos."""
import io
import os
import urllib.request

from PIL import Image, ImageDraw, ImageFont, ImageOps

from .http import USER_AGENT

W, H = 1080, 1350
RED = (161, 20, 15)
CREAM = (247, 241, 230)
INK = (12, 25, 47)  # NA Beer Market navy
HERE = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(HERE, "..", "assets", "logo-market.png")
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
    lines = lines + [line] if line else lines
    if len(lines) == 2:  # balance two lines so one word isn't left alone
        words = text.split()
        best = min(range(1, len(words)), key=lambda i: max(
            draw.textlength(" ".join(words[:i]), font=font),
            draw.textlength(" ".join(words[i:]), font=font)))
        lines = [" ".join(words[:best]), " ".join(words[best:])]
    return lines


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
        logo = ImageOps.contain(logo, (250, 140))
        img.paste(logo, (60, H - 170 + (170 - logo.height) // 2), logo)
        fx = 60 + logo.width + 30
    except OSError:
        fx = 60
    ff = _font(34)
    d.text((fx, H - 105), footer, font=ff, fill=INK)

    img.save(out_path, "PNG", optimize=True)
    return out_path


def beer_slide(beer, index, total, out_path, footer="Shop at nabeermarket.com", fetch=_fetch):
    """One carousel slide per beer: big photo, name, style and price."""
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)

    # Photo panel
    top, side, panel_h = 60, 60, 820
    mask = Image.new("L", (W - 2 * side, panel_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, W - 2 * side - 1, panel_h - 1], radius=28, fill=255)
    try:
        photo = ImageOps.fit(fetch(beer["image"]), (W - 2 * side, panel_h), centering=(0.5, 0.5))
    except Exception as e:
        print(f"warning: could not load {beer['image']}: {e}")
        photo = Image.new("RGB", (W - 2 * side, panel_h), "white")
    img.paste(photo, (side, top), mask)

    # Counter chip
    chip = _font(30)
    label = f"{index}/{total}"
    cw = d.textlength(label, font=chip) + 36
    d.rounded_rectangle([W - side - cw - 20, top + 20, W - side - 20, top + 74], radius=27, fill=RED)
    d.text((W - side - cw - 2, top + 30), label, font=chip, fill="white")

    # Name (up to two lines), then style and price
    y = top + panel_h + 36
    size = 58
    while size > 36:
        nf = _font(size)
        lines = _wrap(d, beer["name"], nf, W - 2 * side)
        if len(lines) <= 2:
            break
        size -= 4
    for ln in lines[:2]:
        d.text((side, y), ln, font=nf, fill=INK)
        y += size + 10
    meta = ", ".join(beer.get("styles", [])[:2]) or "NA beer"
    if beer.get("price"):
        meta += f"  ·  ${float(beer['price']):.2f} a can"
    d.text((side, y + 8), meta.upper(), font=_font(30), fill=RED)

    # Footer
    d.rectangle([0, H - 110, W, H], fill="white")
    try:
        logo = ImageOps.contain(Image.open(LOGO).convert("RGBA"), (170, 90))
        img.paste(logo, (side, H - 110 + (110 - logo.height) // 2), logo)
        fx = side + logo.width + 24
    except OSError:
        fx = side
    d.text((fx, H - 74), footer, font=_font(32), fill=INK)
    img.save(out_path, "PNG", optimize=True)
    return out_path
