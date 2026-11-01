"""Choose the week's theme and beers. Pure functions, no network, so it's testable."""
import datetime as dt
import html
import random
import re


def brand_of(name):
    """Rough brand key: the first word of the product name ("Athletic", "Go")."""
    return (name.split() or ["?"])[0].lower()


def theme_for(date, config, override=None):
    """Return (theme_key, label). Seasonal windows win over the rotation."""
    if override:
        return override, config["themes"][override]["label"]
    md = date.strftime("%m-%d")
    for s in config.get("seasonal", []):
        lo, hi = s["from"], s["to"]
        inside = lo <= md <= hi if lo <= hi else (md >= lo or md <= hi)
        if inside:
            return s["theme"], s["label"]
    rot = config["rotation"]
    key = rot[date.isocalendar()[1] % len(rot)]
    return key, config["themes"][key]["label"]


def recently_featured(featured, date, weeks):
    cutoff = date - dt.timedelta(weeks=weeks)
    return {f["product_id"] for f in featured
            if dt.date.fromisoformat(f["week"]) > cutoff}


def eligible(products, config, featured_ids):
    out = []
    excl_ids = set(config.get("always_exclude_product_ids", []))
    excl_names = [s.lower() for s in config.get("always_exclude_name_contains", [])]
    for p in products:
        if p.get("status", "publish") != "publish" or p.get("stock_status") != "instock":
            continue
        if p["id"] in excl_ids or p["id"] in featured_ids:
            continue
        if any(s in p["name"].lower() for s in excl_names):
            continue
        if not p.get("images"):
            continue
        qty = p.get("stock_quantity")
        if p.get("manage_stock") and (qty is None or qty < config["min_stock"]):
            continue
        out.append(p)
    return out


def _in_categories(p, slugs):
    return any(c.get("slug") in slugs for c in p.get("categories", []))


def _ordered(pool, theme, config, rng):
    sort = theme.get("sort")
    if theme.get("categories"):
        pool = [p for p in pool if _in_categories(p, set(theme["categories"]))]
    if sort == "newest":
        return sorted(pool, key=lambda p: p.get("date_created", ""), reverse=True)
    if sort == "lowest_stock":
        return sorted(pool, key=lambda p: (p.get("stock_quantity") or 0, p["name"]))
    pool = sorted(pool, key=lambda p: p["id"])
    rng.shuffle(pool)
    return pool


def pick(products, theme_key, config, date, featured):
    """Return up to beers_per_week products for the theme, respecting the rules."""
    rng = random.Random(date.isoformat())
    pool = eligible(products, config, recently_featured(featured, date, config["no_repeat_weeks"]))
    theme = config["themes"][theme_key]
    n, cap = config["beers_per_week"], config["max_per_brand"]

    if theme.get("sort") == "mixed_styles":
        queues = [_ordered(pool, config["themes"][k], config, rng) for k in theme["mix"]]
        ordered, seen = [], set()
        while any(queues):
            for q in queues:
                while q:
                    p = q.pop(0)
                    if p["id"] not in seen:
                        seen.add(p["id"])
                        ordered.append(p)
                        break
    else:
        ordered = _ordered(pool, theme, config, rng)

    chosen, per_brand = [], {}
    for p in ordered:
        b = brand_of(p["name"])
        if per_brand.get(b, 0) >= cap:
            continue
        chosen.append(p)
        per_brand[b] = per_brand.get(b, 0) + 1
        if len(chosen) == n:
            break
    return chosen


def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", " ", s or "")).split()


def summarize(p):
    """The fields the copywriter (and the post template) need for one beer."""
    words = strip_tags(p.get("description"))
    return {
        "id": p["id"],
        "name": html.unescape(p["name"]),
        "brand": brand_of(html.unescape(p["name"])),
        "price": p.get("price"),
        "permalink": p["permalink"],
        "image": p["images"][0]["src"],
        "styles": [html.unescape(c["name"]) for c in p.get("categories", [])
                   if c.get("slug") != "uncategorized"],
        "stock_quantity": p.get("stock_quantity"),
        "description_excerpt": " ".join(words[:90]),
    }
