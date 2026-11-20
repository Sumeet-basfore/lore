"""AT Protocol Bluesky publisher with exact UTF-8 byte offset facet slicing."""

import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from lore.publishing.base import PublishResult


def compute_byte_facets(text: str) -> List[Dict[str, Any]]:
    """Computes exact UTF-8 byte offsets for URLs and mentions in AT Protocol."""
    facets: List[Dict[str, Any]] = []
    text_bytes = text.encode("utf-8")

    # Match URLs
    url_pattern = re.compile(rb"https?://[^\s]+", re.IGNORECASE)
    for match in url_pattern.finditer(text_bytes):
        url_str = match.group(0).decode("utf-8")
        facets.append(
            {
                "index": {"byteStart": match.start(), "byteEnd": match.end()},
                "features": [{"$type": "app.bsky.richtext.facet#link", "uri": url_str}],
            }
        )

    # Match Mentions (@handle.bsky.social)
    mention_pattern = re.compile(rb"@([a-zA-Z0-9\.\-]+)", re.IGNORECASE)
    for match in mention_pattern.finditer(text_bytes):
        handle_str = match.group(1).decode("utf-8")
        facets.append(
            {
                "index": {"byteStart": match.start(), "byteEnd": match.end()},
                "features": [{"$type": "app.bsky.richtext.facet#mention", "did": f"did:plc:{handle_str}"}],
            }
        )

    return facets


class BlueskyPublisher:
    """Publishes skeets to Bluesky via AT Protocol com.atproto.repo.createRecord."""

    BSKY_ENDPOINT = "https://bsky.social/xrpc"

    @classmethod
    def publish(
        cls,
        content: str,
        image_path: Optional[str] = None,
        handle: Optional[str] = None,
        app_password: Optional[str] = None,
    ) -> PublishResult:
        user = handle or os.getenv("BLUESKY_HANDLE")
        password = app_password or os.getenv("BLUESKY_APP_PASSWORD")

        if not user or not password or os.getenv("LORE_MOCK_LLM", "0") == "1":
            return PublishResult(
                success=True,
                platform="bluesky",
                published_url="https://bsky.app/profile/user.bsky.social/post/mock12345",
            )

        with httpx.Client(timeout=30.0) as client:
            # 1. Create Session
            sess_resp = client.post(
                f"{cls.BSKY_ENDPOINT}/com.atproto.server.createSession",
                json={"identifier": user, "password": password},
            )
            sess_resp.raise_for_status()
            sess_data = sess_resp.json()
            access_jwt = sess_data["accessJwt"]
            did = sess_data["did"]

            headers = {"Authorization": f"Bearer {access_jwt}"}

            # 2. Upload image blob if present
            embed = None
            if image_path and Path(image_path).is_file():
                img_data = Path(image_path).read_bytes()
                if len(img_data) <= 1000000:
                    blob_resp = client.post(
                        f"{cls.BSKY_ENDPOINT}/com.atproto.repo.uploadBlob",
                        headers={**headers, "Content-Type": "image/png"},
                        content=img_data,
                    )
                    if blob_resp.is_success:
                        blob = blob_resp.json().get("blob")
                        if blob:
                            embed = {
                                "$type": "app.bsky.embed.images",
                                "images": [{"alt": "Code Diff Card", "image": blob}],
                            }

            # 3. Create post record with exact byte facets
            facets = compute_byte_facets(content)
            now_iso = datetime.now(timezone.utc).isoformat()
            record: Dict[str, Any] = {
                "$type": "app.bsky.feed.post",
                "text": content,
                "createdAt": now_iso,
            }
            if facets:
                record["facets"] = facets
            if embed:
                record["embed"] = embed

            post_resp = client.post(
                f"{cls.BSKY_ENDPOINT}/com.atproto.repo.createRecord",
                headers=headers,
                json={"repo": did, "collection": "app.bsky.feed.post", "record": record},
            )
            post_resp.raise_for_status()
            r_data = post_resp.json()
            rkey = r_data.get("uri", "").split("/")[-1]

            return PublishResult(
                success=True,
                platform="bluesky",
                published_url=f"https://bsky.app/profile/{user}/post/{rkey}",
            )
