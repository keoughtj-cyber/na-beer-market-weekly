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


def _paras(text):
    out = []
    for chunk in text.strip().split("\n\n"):
        chunk = html.escape(chunk.strip()).replace("\n", "<br>")
        if chunk:
            out.append(f"<!-- wp:paragraph -->\n<p>{chunk}</p>\n<!-- /wp:paragraph -->")
    return out


def _button(text, url):
    return (
        "<!-- wp:buttons -->\n<div class=\"wp-block-buttons\"><!-- wp:button -->\n"
        f"<div class=\"wp-block-button\"><a class=\"wp-block-button__link wp-element-button\" "
        f"href=\"{html.escape(url, quote=True)}\">{html.escape(text)}</a></div>\n"
        "<!-- /wp:button --></div>\n<!-- /wp:buttons -->"
    )


def build_post_html(plan, copy, cta):
    blocks = _paras(copy["intro"])
    for b in plan["beers"]:
        url = html.escape(b["permalink"], quote=True)
        name = html.escape(b["name"])
        blocks.append(
            "<!-- wp:heading -->\n"
            f"<h2 class=\"wp-block-heading\"><a href=\"{url}\">{name}</a></h2>\n"
            "<!-- /wp:heading -->"
        )
        blocks.append(
            "<!-- wp:image {\"sizeSlug\":\"medium\",\"linkDestination\":\"custom\"} -->\n"
            f"<figure class=\"wp-block-image size-medium\"><a href=\"{url}\">"
            f"<img src=\"{html.escape(b['image'], quote=True)}\" alt=\"{name} non-alcoholic beer\"/>"
            "</a></figure>\n<!-- /wp:image -->"
        )
        style = html.escape(", ".join(b["styles"][:2])) if b["styles"] else "NA beer"
        price = f"${float(b['price']):.2f} a can" if b.get("price") else ""
        meta = " · ".join(x for x in [style, price] if x)
        blocks.append(f"<!-- wp:paragraph -->\n<p><strong>{meta}</strong></p>\n<!-- /wp:paragraph -->")
        blocks.extend(_paras(copy["blurbs"][str(b["id"])]))
        blocks.append(_button(f"Shop {b['name']}", b["permalink"]))
    blocks.extend(_paras(copy["outro"]))
    blocks.append(_button(cta["text"], cta["url"]))
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
