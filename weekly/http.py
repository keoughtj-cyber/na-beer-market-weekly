"""Small stdlib HTTP helper with retries.

The Market host returns 406 to Python's default User-Agent, so every request
sends a curl-like one.
"""
import base64
import json
import time
import urllib.error
import urllib.request

USER_AGENT = "curl/8.5.0 (na-beer-market-weekly)"


class HTTPError(RuntimeError):
    def __init__(self, status, body, url):
        super().__init__(f"HTTP {status} from {url}: {body[:500]}")
        self.status = status
        self.body = body


def request(method, url, *, auth=None, bearer=None, json_body=None, data=None,
            headers=None, retries=4, timeout=60):
    hdrs = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if auth:
        token = base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
        hdrs["Authorization"] = f"Basic {token}"
    if bearer:
        hdrs["Authorization"] = f"Bearer {bearer}"
    if json_body is not None:
        data = json.dumps(json_body).encode()
        hdrs["Content-Type"] = "application/json"
    hdrs.update(headers or {})

    delay = 2
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
                ctype = resp.headers.get("Content-Type", "")
                body = json.loads(raw) if "json" in ctype and raw else raw
                return body, dict(resp.headers)
        except urllib.error.HTTPError as e:
            text = e.read().decode("utf-8", "replace")
            retryable = e.code in (403, 408, 429, 500, 502, 503, 504)
            if retryable and attempt < retries:
                time.sleep(delay)
                delay *= 2
                continue
            raise HTTPError(e.code, text, url) from None
        except (urllib.error.URLError, TimeoutError):
            if attempt < retries:
                time.sleep(delay)
                delay *= 2
                continue
            raise
