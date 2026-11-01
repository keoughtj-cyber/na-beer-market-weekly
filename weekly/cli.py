"""Command line: pick -> (write copy.json) -> draft -> publish.

  python -m weekly pick    [--date YYYY-MM-DD] [--theme KEY]
  python -m weekly draft   --date YYYY-MM-DD [--dry-run]
  python -m weekly publish --date YYYY-MM-DD --approved-by NAME [--dry-run]
  python -m weekly buffer-channels

--date is the Thursday the week goes live (defaults to the next one).
Nothing here publishes without `publish --approved-by`, and even then the post
is *scheduled* for the configured day and time, not pushed out immediately.
"""
import argparse
import datetime as dt
import json
import os
import sys
from zoneinfo import ZoneInfo

from . import pick as picker
from . import render

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
SOCIAL_DELAY = dt.timedelta(minutes=15)  # socials go out after the post is live


def load_json(path, default=None):
    if not os.path.exists(path):
        if default is not None:
            return default
        raise SystemExit(f"missing {os.path.relpath(path, ROOT)}")
    with open(path) as f:
        return json.load(f)


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def config():
    return load_json(os.path.join(ROOT, "config.json"))


def next_publish_date(cfg, today=None):
    today = today or dt.datetime.now(ZoneInfo(cfg["timezone"])).date()
    target = WEEKDAYS.index(cfg["publish_weekday"])
    days = (target - today.weekday()) % 7 or 7
    return today + dt.timedelta(days=days)


def publish_at(cfg, date):
    h, m = map(int, cfg["publish_time"].split(":"))
    return dt.datetime.combine(date, dt.time(h, m), ZoneInfo(cfg["timezone"]))


def week_dir(date):
    return os.path.join(ROOT, "weeks", date.isoformat())


# Commands -------------------------------------------------------------------

def cmd_pick(args):
    from .market import Market
    cfg = config()
    date = dt.date.fromisoformat(args.date) if args.date else next_publish_date(cfg)
    theme, label = picker.theme_for(date, cfg, args.theme)
    featured = load_json(os.path.join(ROOT, "state", "featured.json"), [])
    products = Market(cfg["market_base"]).in_stock_products()
    chosen = picker.pick(products, theme, cfg, date, featured)
    if len(chosen) < 3:
        raise SystemExit(f"only {len(chosen)} eligible beers for theme {theme}; try --theme")
    plan = {
        "date": date.isoformat(),
        "publish_at": publish_at(cfg, date).isoformat(),
        "theme": theme,
        "theme_label": label,
        "beers": [picker.summarize(p) for p in chosen],
    }
    save_json(os.path.join(week_dir(date), "plan.json"), plan)
    print(json.dumps(plan, indent=2, ensure_ascii=False))
    print(f"\nNext: write weeks/{date}/copy.json (see COPY_GUIDE.md), then run draft.")


def cmd_draft(args):
    cfg = config()
    date = dt.date.fromisoformat(args.date)
    wd = week_dir(date)
    plan = load_json(os.path.join(wd, "plan.json"))
    copy = load_json(os.path.join(wd, "copy.json"))
    render.validate_copy(copy, plan)
    out = load_json(os.path.join(wd, "out.json"), {})

    from .image import compose
    img_path = os.path.join(wd, f"na-beer-market-weekly-picks-{date}.png")
    compose(copy["image_headline"], [b["image"] for b in plan["beers"]], img_path,
            footer=f"Shop at {cfg['display_domain']}")
    body = render.build_post_html(plan, copy, cfg["cta"])
    with open(os.path.join(wd, "preview.html"), "w") as f:
        f.write(render.preview_page(copy["title"], body))
    if args.dry_run:
        print(f"dry run: wrote {os.path.relpath(wd, ROOT)}/preview.html and the social image")
        return

    from .market import Market
    m = Market(cfg["market_base"])
    if out.get("status") == "scheduled":
        raise SystemExit("this week is already scheduled; edit it in WordPress instead")
    cat = m.ensure_category(cfg["post_category"]["name"], cfg["post_category"]["slug"])
    if not out.get("media_id"):
        media = m.upload_media(img_path, f"{copy['image_headline']}: non-alcoholic beers at NA Beer Market",
                               f"Weekly picks {date}")
        out.update(media_id=media["id"], media_url=media["source_url"])
    fields = {
        "title": copy["title"], "content": body, "excerpt": copy["excerpt"],
        "status": "draft", "categories": [cat], "featured_media": out["media_id"],
    }
    if copy.get("slug"):
        fields["slug"] = copy["slug"]
    post = m.save_post(out.get("post_id"), fields)
    out.update(post_id=post["id"], status="draft",
               edit_link=f"{cfg['market_base']}/wp-admin/post.php?post={post['id']}&action=edit",
               preview_link=f"{cfg['market_base']}/?p={post['id']}&preview=true")
    save_json(os.path.join(wd, "out.json"), out)
    print(json.dumps(out, indent=2))


def cmd_publish(args):
    cfg = config()
    date = dt.date.fromisoformat(args.date)
    wd = week_dir(date)
    plan = load_json(os.path.join(wd, "plan.json"))
    copy = load_json(os.path.join(wd, "copy.json"))
    out = load_json(os.path.join(wd, "out.json"))
    render.validate_copy(copy, plan)
    if out.get("status") == "scheduled":
        raise SystemExit("already scheduled")
    when = publish_at(cfg, date)
    if when <= dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=10):
        raise SystemExit(f"publish time {when} has passed; pick a new --date")
    when_utc = when.astimezone(dt.timezone.utc)
    social_utc = (when_utc + SOCIAL_DELAY).strftime("%Y-%m-%dT%H:%M:%SZ")

    if args.dry_run:
        print(f"dry run: would schedule post {out['post_id']} for {when} "
              f"and Buffer posts for {social_utc} on {cfg['buffer']['services']}")
        return

    from .buffer import Buffer
    from .market import Market
    buf = Buffer()
    channels = buf.resolve_channels(cfg)  # fail early, before touching WordPress
    m = Market(cfg["market_base"])
    post = m.save_post(out["post_id"], {
        "status": "future", "date_gmt": when_utc.strftime("%Y-%m-%dT%H:%M:%S")})
    link = post["link"]
    out.update(status="scheduling", link=link, approved_by=args.approved_by,
               approved_at=dt.datetime.now(dt.timezone.utc).isoformat())
    save_json(os.path.join(wd, "out.json"), out)

    texts = {"instagram": copy["instagram_caption"],
             "facebook": copy["facebook_caption"].replace("{url}", link)}
    out.setdefault("buffer", {})
    for service, cid in channels.items():
        if service in out["buffer"]:
            continue
        p = buf.create_post(cid, texts.get(service, texts["facebook"]), out["media_url"],
                            social_utc, (cfg["buffer"].get("extra_input") or {}).get(service))
        out["buffer"][service] = p
        save_json(os.path.join(wd, "out.json"), out)

    out["status"] = "scheduled"
    save_json(os.path.join(wd, "out.json"), out)
    featured_path = os.path.join(ROOT, "state", "featured.json")
    featured = load_json(featured_path, [])
    featured += [{"week": date.isoformat(), "product_id": b["id"], "name": b["name"]}
                 for b in plan["beers"]]
    save_json(featured_path, featured)
    print(json.dumps(out, indent=2))


def cmd_buffer_test(args):
    """Save this week's captions + image to Buffer as DRAFTS (never published)."""
    from .buffer import Buffer
    cfg = config()
    wd = week_dir(dt.date.fromisoformat(args.date))
    copy = load_json(os.path.join(wd, "copy.json"))
    out = load_json(os.path.join(wd, "out.json"))
    buf = Buffer()
    texts = {"instagram": copy["instagram_caption"],
             "facebook": copy["facebook_caption"].replace("{url}", out.get("link") or cfg["cta"]["url"])}
    for service, cid in buf.resolve_channels(cfg).items():
        p = buf.create_post(cid, "[TEST DRAFT] " + texts[service], out["media_url"], draft=True,
                            extra=(cfg["buffer"].get("extra_input") or {}).get(service))
        print(f"{service}: draft {p['id']} status={p['status']}")


def cmd_buffer_channels(args):
    from .buffer import Buffer
    for ch in Buffer().channels():
        print(f"{ch['service']:<12} {ch['id']}  {ch.get('displayName') or ch['name']}"
              f"{'  (disconnected)' if ch['isDisconnected'] else ''}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="weekly")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pick"); p.add_argument("--date"); p.add_argument("--theme")
    p.set_defaults(fn=cmd_pick)
    p = sub.add_parser("draft"); p.add_argument("--date", required=True)
    p.add_argument("--dry-run", action="store_true"); p.set_defaults(fn=cmd_draft)
    p = sub.add_parser("publish"); p.add_argument("--date", required=True)
    p.add_argument("--approved-by", required=True,
                   help="who approved this week's preview (recorded in out.json)")
    p.add_argument("--dry-run", action="store_true"); p.set_defaults(fn=cmd_publish)
    p = sub.add_parser("buffer-channels"); p.set_defaults(fn=cmd_buffer_channels)
    p = sub.add_parser("buffer-test", help="save this week's posts to Buffer as drafts only")
    p.add_argument("--date", required=True); p.set_defaults(fn=cmd_buffer_test)
    args = ap.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main(sys.argv[1:])
