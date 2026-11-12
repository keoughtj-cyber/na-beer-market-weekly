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


# ---- Email version -------------------------------------------------------
# Mailchimp's RSS campaign pastes *|RSSITEM:CONTENT_FULL|* into
# email/mailchimp-rss-template.html. The web post's flex layout looks poor on
# phones, so `draft` also saves this table-based, phone-first version as post
# meta "nabc_email_html", and a Market Code Snippet ("Weekly picks: email
# version in feed") serves that meta in the RSS feed instead of the web body.
# House email look: cream, red bar, Georgia, red pill buttons.

E_RED = "#b21a19"
INK = "#2b2b2b"
CREAM = "#f3ece0"
CARD = "#f8f3ea"
SERIF = "Georgia,'Times New Roman',serif"
SANS = "Arial,Helvetica,sans-serif"


def _p(text, size=17, lh=27, color=INK, margin="0 0 14px", align="left"):
    out = []
    for chunk in text.strip().split("\n\n"):
        chunk = html.escape(chunk.strip()).replace("\n", "<br>")
        if chunk:
            out.append(f'<p style="margin:{margin};font-family:{SERIF};font-size:{size}px;'
                       f'line-height:{lh}px;color:{color};text-align:{align}">{chunk}</p>')
    return "".join(out)


def _pill(text, url, block=False):
    disp = "display:block;text-align:center" if block else "display:inline-block"
    return (f'<a href="{html.escape(url, quote=True)}" style="{disp};background:{E_RED};color:#ffffff;'
            f'font-family:{SANS};font-size:16px;font-weight:bold;text-decoration:none;'
            f'padding:14px 28px;border-radius:30px">{html.escape(text)}</a>')


def _utm(url, campaign):
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}utm_source=mailchimp&utm_medium=email&utm_campaign={campaign}"


def beer_card(b, blurb, campaign):
    url = _utm(b["permalink"], campaign)
    u = html.escape(url, quote=True)
    name = html.escape(b["name"])
    style = html.escape(", ".join(b["styles"][:2])) if b.get("styles") else "NA beer"
    price = f"${float(b['price']):.2f}" if b.get("price") else ""
    btn = f"Shop this beer &middot; {price}" if price else "Shop this beer"
    return (
        '<tr><td class="px" style="padding:0 20px 16px">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'style="background:{CARD};border-radius:10px"><tr><td class="cardpad" style="padding:22px 22px 24px">'
        f'<a href="{u}"><img src="{html.escape(b["image"], quote=True)}" width="200" '
        f'alt="{name} non-alcoholic beer" style="display:block;margin:0 auto 16px;width:200px;'
        'max-width:100%;height:auto;border:0;border-radius:8px"></a>'
        f'<p style="margin:0 0 4px;font-family:{SERIF};font-size:22px;line-height:28px;font-weight:bold;'
        f'text-align:center"><a href="{u}" style="color:{INK};text-decoration:none">{name}</a></p>'
        f'<p style="margin:0 0 14px;font-family:{SANS};font-size:12px;line-height:18px;font-weight:bold;'
        f'letter-spacing:1px;text-transform:uppercase;color:{E_RED};text-align:center">{style}</p>'
        + _p(blurb, size=16, lh=25, margin="0 0 18px")
        + f'<a href="{u}" style="display:block;text-align:center;background:{E_RED};color:#ffffff;'
        f'font-family:{SANS};font-size:16px;font-weight:bold;text-decoration:none;padding:14px 20px;'
        f'border-radius:30px">{btn}</a>'
        "</td></tr></table></td></tr>"
    )


def build_email_body(plan, copy, cta):
    """The part that replaces *|RSSITEM:CONTENT_FULL|* (a table inside the 600px card)."""
    campaign = f"market-weekly-{plan['date']}"
    rows = [f'<tr><td class="px" style="padding:0 24px 10px">{_p(copy["excerpt"], align="center", color="#555555")}</td></tr>']
    rows += [beer_card(b, copy["blurbs"][str(b["id"])], campaign) for b in plan["beers"]]
    rows.append(
        f'<tr><td class="px" align="center" style="padding:14px 28px 30px">'
        + _p(copy["outro"], size=16, lh=25, align="center", margin="0 0 18px")
        + _pill(cta["text"], _utm(cta["url"], campaign)) + "</td></tr>")
    # One self-contained table, so the feed item is valid HTML on its own.
    return ('<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">'
            + "".join(rows) + "</table>")


def email_preview_page(title, body_rows):
    """The whole email as Mailchimp will send it, with merge tags filled in."""
    import os
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "email", "mailchimp-rss-template.html")
    tpl = open(path, encoding="utf-8").read()
    head, rest = tpl.split("*|RSSITEMS:|*")
    item, tail = rest.split("*|END:RSSITEMS|*")
    item = (item.replace("*|RSSITEM:URL|*", "#").replace("*|RSSITEM:TITLE|*", html.escape(title))
            .replace("*|RSSITEM:CONTENT_FULL|*", body_rows))
    out = head + item + tail
    for tag, val in {"*|MC:SUBJECT|*": html.escape(title), "*|MC_PREVIEW_TEXT|*": "",
                     "*|LIST:ADDRESSLINE|*": "NA Beer Club", "*|UPDATE_PROFILE|*": "#", "*|UNSUB|*": "#"}.items():
        out = out.replace(tag, val)
    return out
