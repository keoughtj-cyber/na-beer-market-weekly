"""market.nabeerclub.com client (WordPress + WooCommerce REST API).

Auth: application password in env vars MARKET_WP_USER / MARKET_WP_APP_PASSWORD.
"""
import os
import urllib.parse

from .http import request


class Market:
    def __init__(self, base):
        self.base = base.rstrip("/")
        user = os.environ.get("MARKET_WP_USER")
        pw = os.environ.get("MARKET_WP_APP_PASSWORD")
        if not user or not pw:
            raise SystemExit("MARKET_WP_USER and MARKET_WP_APP_PASSWORD must be set")
        self.auth = (user, pw)

    def _url(self, path, params=None):
        url = f"{self.base}/wp-json/{path.lstrip('/')}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        return url

    def get(self, path, params=None):
        return request("GET", self._url(path, params), auth=self.auth)[0]

    def post(self, path, body):
        return request("POST", self._url(path), auth=self.auth, json_body=body)[0]

    # Products -----------------------------------------------------------
    def in_stock_products(self):
        out, page = [], 1
        while True:
            batch = self.get("wc/v3/products", {
                "status": "publish", "stock_status": "instock",
                "per_page": 100, "page": page,
            })
            out.extend(batch)
            if len(batch) < 100:
                return out
            page += 1

    # Posts --------------------------------------------------------------
    def ensure_category(self, name, slug):
        found = self.get("wp/v2/categories", {"slug": slug})
        if found:
            return found[0]["id"]
        return self.post("wp/v2/categories", {"name": name, "slug": slug})["id"]

    def upload_media(self, path, alt_text, title):
        filename = os.path.basename(path)
        with open(path, "rb") as f:
            data = f.read()
        media, _ = request(
            "POST", self._url("wp/v2/media"), auth=self.auth, data=data,
            headers={"Content-Type": "image/png",
                     "Content-Disposition": f'attachment; filename="{filename}"'},
        )
        self.post(f"wp/v2/media/{media['id']}", {"alt_text": alt_text, "title": title})
        return media

    def save_post(self, post_id, fields):
        path = f"wp/v2/posts/{post_id}" if post_id else "wp/v2/posts"
        return self.post(path, fields)

    def get_post(self, post_id):
        return self.get(f"wp/v2/posts/{post_id}", {"context": "edit"})
