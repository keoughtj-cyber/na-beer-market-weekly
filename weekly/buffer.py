"""Buffer GraphQL API client (https://api.buffer.com, public beta since Feb 2026).

Auth: personal API key in env var BUFFER_API_KEY.
"""
import os

from .http import request

API = "https://api.buffer.com"


class Buffer:
    def __init__(self):
        self.key = os.environ.get("BUFFER_API_KEY")
        if not self.key:
            raise SystemExit("BUFFER_API_KEY must be set")

    def gql(self, query, variables=None):
        body, _ = request("POST", API, bearer=self.key,
                          json_body={"query": query, "variables": variables or {}})
        if body.get("errors"):
            raise RuntimeError("; ".join(e.get("message", "?") for e in body["errors"]))
        return body["data"]

    def channels(self):
        orgs = self.gql("{ account { organizations { id name } } }")["account"]["organizations"]
        out = []
        for org in orgs:
            out += self.gql(
                """query($input: ChannelsInput!) { channels(input: $input) {
                     id name displayName service isDisconnected isQueuePaused timezone } }""",
                {"input": {"organizationId": org["id"]}},
            )["channels"]
        return out

    def resolve_channels(self, config):
        """Map service name -> channel id, using config overrides first."""
        wanted = config["buffer"]["services"]
        ids = dict(config["buffer"].get("channel_ids") or {})
        if all(s in ids for s in wanted):
            return ids
        for ch in self.channels():
            if ch["service"] in wanted and ch["service"] not in ids and not ch["isDisconnected"]:
                ids[ch["service"]] = ch["id"]
        missing = [s for s in wanted if s not in ids]
        if missing:
            raise SystemExit(f"No connected Buffer channel for: {', '.join(missing)}")
        return ids

    def create_post(self, channel_id, text, image_urls, due_at_iso=None, extra=None, draft=False):
        """Schedule a post for due_at_iso, or with draft=True save it as a Buffer
        draft that never publishes until someone schedules it in Buffer."""
        payload = {
            "channelId": channel_id,
            "text": text,
            "schedulingType": "automatic",
            "assets": [{"image": {"url": u}} for u in image_urls][:10],  # carousel, max 10
        }
        if draft:
            payload.update(mode="addToQueue", saveToDraft=True)
        else:
            payload.update(mode="customScheduled", dueAt=due_at_iso)
        payload.update(extra or {})
        data = self.gql(
            """mutation($input: CreatePostInput!) { createPost(input: $input) {
                 ... on PostActionSuccess { post { id status dueAt } }
                 ... on MutationError { message } } }""",
            {"input": payload},
        )["createPost"]
        if "message" in data:
            raise RuntimeError(f"Buffer refused the post: {data['message']}")
        return data["post"]
