import datetime as dt
import json
import os
import tempfile
import unittest

from PIL import Image

from weekly import pick, render
from weekly.cli import next_publish_date, publish_at
from weekly.image import beer_slide, compose

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, "config.json")))


def product(pid, name, slug="pilsner", qty=50, date="2026-10-01", **kw):
    p = {"id": pid, "name": name, "status": "publish", "stock_status": "instock",
         "manage_stock": True, "stock_quantity": qty, "date_created": date,
         "price": "4.49", "permalink": f"https://m/{pid}/",
         "images": [{"src": f"https://m/{pid}.jpg"}],
         "categories": [{"name": slug.title(), "slug": slug}], "description": "<p>Tasty.</p>"}
    p.update(kw)
    return p


class PickTests(unittest.TestCase):
    def test_seasonal_beats_rotation(self):
        self.assertEqual(pick.theme_for(dt.date(2026, 11, 26), CFG)[0], "occasion")
        self.assertEqual(pick.theme_for(dt.date(2027, 1, 7), CFG)[1], "New Year and Dry January")
        self.assertIn(pick.theme_for(dt.date(2026, 11, 5), CFG)[0], CFG["rotation"])

    def test_filters_low_stock_test_items_and_recent(self):
        prods = [product(1, "A Pils", qty=3), product(2, "Test Beer 123"),
                 product(3, "B Pils"), product(4, "C Pils", images=[]), product(5, "D Pils")]
        featured = [{"week": "2026-10-29", "product_id": 5, "name": "D Pils"}]
        got = pick.pick(prods, "crisp", CFG, dt.date(2026, 11, 5), featured)
        self.assertEqual([p["id"] for p in got], [3])

    def test_old_features_can_return(self):
        featured = [{"week": "2026-08-01", "product_id": 3, "name": "B Pils"}]
        got = pick.pick([product(3, "B Pils")], "crisp", CFG, dt.date(2026, 11, 5), featured)
        self.assertEqual(len(got), 1)

    def test_brand_cap_and_newest(self):
        prods = [product(i, f"Athletic Beer {i}", date=f"2026-10-{10 + i}") for i in range(4)]
        prods.append(product(9, "Go Beer", date="2026-01-01"))
        got = pick.pick(prods, "new-arrivals", CFG, dt.date(2026, 11, 5), [])
        self.assertEqual([p["id"] for p in got], [3, 2, 9])

    def test_mixed_styles_spreads_styles(self):
        prods = [product(1, "A Lager", "lager"), product(2, "B IPA", "ipa"),
                 product(3, "C Stout", "porter"), product(4, "D Radler", "radler")]
        got = pick.pick(prods, "occasion", CFG, dt.date(2026, 11, 20), [])
        self.assertEqual({p["id"] for p in got}, {1, 2, 3, 4})


class RenderTests(unittest.TestCase):
    plan = {"beers": [pick.summarize(product(7, "Go <Brewing> Pils"))]}
    copy = {"title": "T", "excerpt": "E", "intro": "Hi\n\nThere", "blurbs": {"7": "Nice & crisp, with a clean finish that works with almost anything on the table."},
            "outro": "Bye", "image_headline": "H", "instagram_caption": "IG",
            "facebook_caption": "FB {url}"}

    def test_escapes_and_links(self):
        out = render.build_post_html(self.plan, self.copy, CFG["cta"])
        self.assertIn("Go &lt;Brewing&gt; Pils", out)
        self.assertIn("Nice &amp; crisp", out)
        self.assertIn('href="https://m/7/"', out)
        self.assertIn(CFG["cta"]["url"], out)
        self.assertEqual(out.count("<p style="), 5)

    def test_lint_blocks_banned_phrases(self):
        with self.assertRaises(SystemExit):
            render.validate_copy(dict(self.copy, intro="Get a buzz without the booze"), self.plan)
        with self.assertRaises(SystemExit):
            render.validate_copy(dict(self.copy, outro="Price {price} here"), self.plan)

    def test_validate_catches_missing_blurb_and_url(self):
        bad = dict(self.copy, blurbs={})
        with self.assertRaises(SystemExit):
            render.validate_copy(bad, self.plan)
        with self.assertRaises(SystemExit):
            render.validate_copy(dict(self.copy, facebook_caption="no link"), self.plan)
        render.validate_copy(self.copy, self.plan)


class ScheduleTests(unittest.TestCase):
    def test_next_thursday_10am_eastern(self):
        d = next_publish_date(CFG, dt.date(2026, 11, 2))  # Monday
        self.assertEqual(d, dt.date(2026, 11, 5))
        self.assertEqual(next_publish_date(CFG, dt.date(2026, 11, 5)), dt.date(2026, 11, 12))
        self.assertEqual(publish_at(CFG, d).isoformat(), "2026-11-05T10:00:00-05:00")


class ImageTests(unittest.TestCase):
    def test_compose_without_network(self):
        fake = lambda url: Image.new("RGB", (400, 600), "orange")
        with tempfile.TemporaryDirectory() as td:
            out = compose("A headline", ["a", "b", "c", "d", "e"], os.path.join(td, "x.png"), fetch=fake)
            with Image.open(out) as im:
                self.assertEqual(im.size, (1080, 1350))
            beer = {"name": "A Very Long Brewery Name Hazy Non-Alcoholic IPA Special", "image": "x",
                    "styles": ["Hazy IPA"], "price": "4.49"}
            out = beer_slide(beer, 2, 5, os.path.join(td, "s.png"), fetch=fake)
            with Image.open(out) as im:
                self.assertEqual(im.size, (1080, 1350))


if __name__ == "__main__":
    unittest.main()
