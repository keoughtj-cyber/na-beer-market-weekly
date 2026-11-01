"""Build the blog post (Gutenberg block HTML) from plan.json + copy.json.

Copy fields are plain text and get escaped, so nothing in copy.json can inject
markup. A blank line in a text field starts a new paragraph.
"""
import html

REQUIRED_COPY = ["title", "excerpt", "intro", "blurbs", "outro",
                 "image_headline", "instagram_caption", "facebook_caption"]


def validate_copy(copy, plan):
    missing = [k for k in REQUIRED_COPY if not copy.get(k)]
    if missing:
        raise SystemExit(f"copy.json is missing: {', '.join(missing)}")
    ids = {str(b["id"]) for b in plan["beers"]}
    no_blurb = ids - set(map(str, copy["blurbs"]))
    if no_blurb:
        raise SystemExit(f"copy.json has no blurb for product ids: {sorted(no_blurb)}")
    if "{url}" not in copy["facebook_caption"]:
        raise SystemExit("facebook_caption must contain {url} where the post link goes")
    if len(copy["instagram_caption"]) > 2200:
        raise SystemExit("instagram_caption is over Instagram's 2,200 character limit")
    lint_copy(copy)


# Phrases that must never ship: off-brand for a non-alcoholic store, health
# claims, or leftovers from drafting. Checked automatically because nothing is
# reviewed by a person before publishing.
BANNED = ["drunk", "buzzed", "get a buzz", "wasted", "hangover cure", "detox", "cures",
          "healthy", "health benefits", "lorem ipsum", "todo", "tbd", "xxx",
          "[insert", "as an ai"]


def lint_copy(copy):
    texts = [copy["title"], copy["excerpt"], copy["intro"], copy["outro"],
             copy["image_headline"], copy["instagram_caption"],
             copy["facebook_caption"].replace("{url}", "")] + list(copy["blurbs"].values())
    joined = "\n".join(texts).lower()
    hits = [b for b in BANNED if b in joined]
    if hits:
        raise SystemExit(f"copy.json contains banned phrases: {hits}")
    if "{" in joined or "}" in joined:
        raise SystemExit("copy.json has a leftover {placeholder}")
    short = [k for k, v in copy["blurbs"].items() if len(v.strip()) < 60]
    if short:
        raise SystemExit(f"blurbs too short for product ids: {short}")
    if len(copy["image_headline"]) > 34:
        raise SystemExit("image_headline is over 34 characters")


RED = "#A1140F"
NAVY = "#0C192F"
# The Market runs Divi, which doesn't load the block editor's CSS, so every
# spacing and style rule is inline here rather than relying on block classes.
P_STYLE = "margin:0 0 1.2em;line-height:1.7;font-size:17px"


def _paras(text, style=P_STYLE):
    out = []
    for chunk in text.strip().split("\n\n"):
        chunk = html.escape(chunk.strip()).replace("\n", "<br>")
        if chunk:
            out.append(f'<p style="{style}">{chunk}</p>')
    return out


def _button(text, url):
    return (
        f'<a href="{html.escape(url, quote=True)}" style="display:inline-block;background:{RED};'
        "color:#fff;padding:12px 26px;border-radius:6px;font-weight:700;text-decoration:none;"
        f'letter-spacing:.02em">{html.escape(text)}</a>'
    )


def _html_block(inner):
    return f"<!-- wp:html -->\n{inner}\n<!-- /wp:html -->"


def _beer_card(b, blurb):
    url = html.escape(b["permalink"], quote=True)
    name = html.escape(b["name"])
    style = html.escape(", ".join(b["styles"][:2])) if b["styles"] else "NA beer"
    price = f" &middot; ${float(b['price']):.2f} a can" if b.get("price") else ""
    body = "".join(_paras(blurb))
    return _html_block(
        '<div style="display:flex;flex-wrap:wrap;gap:28px;align-items:flex-start;'
        'padding:36px 0;border-top:1px solid #e6ded0">'
        f'<a href="{url}" style="flex:0 0 220px;max-width:100%">'
        f'<img src="{html.escape(b["image"], quote=True)}" alt="{name} non-alcoholic beer" '
        'style="width:220px;max-width:100%;height:auto;border-radius:10px;display:block"></a>'
        '<div style="flex:1 1 300px;min-width:0">'
        f'<h2 style="margin:0 0 .35em;font-size:26px;line-height:1.25;padding:0">'
        f'<a href="{url}" style="color:{NAVY};text-decoration:none">{name}</a></h2>'
        f'<p style="margin:0 0 1em;font-size:14px;font-weight:700;letter-spacing:.06em;'
        f'text-transform:uppercase;color:{RED}">{style}{price}</p>'
        f"{body}{_button('Shop this beer', b['permalink'])}"
        "</div></div>"
    )


def build_post_html(plan, copy, cta):
    blocks = [_html_block("".join(_paras(copy["intro"])))]
    for b in plan["beers"]:
        blocks.append(_beer_card(b, copy["blurbs"][str(b["id"])]))
    blocks.append(_html_block(
        '<div style="padding:40px 28px;margin:12px 0 0;background:#f7f1e6;border-radius:12px;'
        'text-align:center">' + "".join(_paras(copy["outro"])) + _button(cta["text"], cta["url"])
        + "</div>"))
    return "\n\n".join(blocks) + "\n"


def preview_page(title, body_html):
    return (
        "<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width'>"
        f"<title>{html.escape(title)}</title>"
        "<style>body{font:17px/1.6 system-ui;max-width:720px;margin:2rem auto;padding:0 16px}"
        "img{max-width:300px;height:auto}.wp-block-button__link{display:inline-block;"
        "background:#A1140F;color:#fff;padding:.5em 1em;border-radius:4px;text-decoration:none}</style>"
        f"<h1>{html.escape(title)}</h1>{body_html}"
    )
