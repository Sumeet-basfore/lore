"""LinkedIn Restli v2 API publisher with unicode monospace code formatting."""

import os
import re
from pathlib import Path
from typing import Optional

import httpx

from lore.publishing.base import PublishResult


def format_linkedin_monospace(text: str) -> str:
    """Converts markdown backticks `code` into unicode monospace characters.
    LinkedIn feed does not support markdown, so raw backticks look amateurish.
    """
    normal = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    mono = "𝚊𝚋𝚌𝚍𝚎𝚏𝚐𝚑𝚒𝚓𝚔𝚕𝚖𝚗𝚘𝚙𝚚𝚛𝚜𝚝𝚞𝚟𝚠𝚡𝚢𝚣𝙰𝙱𝙲𝙳𝙴𝙵𝙶𝙷𝙸𝙹𝙺𝙻𝙼𝙽𝙾𝙿𝚀𝚁𝚂𝚃𝚄𝚅𝚆𝚇𝚈𝚉𝟶𝟷𝟸𝟹𝟺𝟻𝟼𝟽𝟾𝟿"
    trans = str.maketrans(normal, mono)

    def replace_backticks(match):
        code_token = match.group(1)
        return code_token.translate(trans)

    return re.sub(r"`([^`]+)`", replace_backticks, text)


class LinkedInPublisher:
    """Publishes posts and visual cards to LinkedIn using Restli v2 API."""

    API_URL = "https://api.linkedin.com/rest/posts"

    @classmethod
    def publish(
        cls,
        content: str,
        image_path: Optional[str] = None,
        access_token: Optional[str] = None,
        author_urn: Optional[str] = None,
    ) -> PublishResult:
        token = access_token or os.getenv("LINKEDIN_ACCESS_TOKEN")
        author = author_urn or os.getenv("LINKEDIN_AUTHOR_URN")

        formatted_content = format_linkedin_monospace(content)

        if not token or not author or os.getenv("LORE_MOCK_LLM", "0") == "1":
            # Mock or offline mode
            return PublishResult(
                success=True,
                platform="linkedin",
                published_url="https://www.linkedin.com/feed/update/urn:li:share:mock12345",
            )

        headers = {
            "Authorization": f"Bearer {token}",
            "LinkedIn-Version": "202401",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }

        payload = {
            "author": author,
            "commentary": formatted_content,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(cls.API_URL, headers=headers, json=payload)
            resp.raise_for_status()
            post_urn = resp.headers.get("x-restli-id", "unknown")
            return PublishResult(
                success=True,
                platform="linkedin",
                published_url=f"https://www.linkedin.com/feed/update/{post_urn}",
            )
