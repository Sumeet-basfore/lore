"""GitHub Releases publisher formatting structured release notes."""

import os
from typing import Optional
import httpx

from lore.core.models import Draft
from lore.publishing.base import PublishOutcome, PublishResult


class GitHubReleasePublisher:
    """Publishes release notes to GitHub Releases via REST API."""

    @classmethod
    def publish(
        cls,
        draft: Draft,
        repo_owner_name: Optional[str] = None,
        github_token: Optional[str] = None,
    ) -> PublishResult:
        token = github_token or os.getenv("GITHUB_TOKEN")
        repo = repo_owner_name or os.getenv("GITHUB_REPOSITORY")

        title = draft.title or "Release Update"
        body = draft.humanized_content
        tag_name = f"v{draft.id[:6]}"

        if os.getenv("LORE_MOCK_PUBLISHING", "0") == "1":
            return PublishResult(
                success=True,
                outcome=PublishOutcome.SIMULATED,
                platform="github",
                message="Simulated GitHub release; no release was created.",
            )

        missing = []
        if not token:
            missing.append("GITHUB_TOKEN")
        if not repo:
            missing.append("GITHUB_REPOSITORY")
        if missing:
            return PublishResult(
                success=False,
                outcome=PublishOutcome.FAILED,
                platform="github",
                error=f"GitHub release publishing requires {', '.join(missing)}.",
            )

        api_url = f"https://api.github.com/repos/{repo}/releases"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        payload = {
            "tag_name": tag_name,
            "name": title,
            "body": body,
            "draft": False,
            "prerelease": False,
        }

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(api_url, headers=headers, json=payload)
            resp.raise_for_status()
            release_data = resp.json()
            return PublishResult(
                success=True,
                outcome=PublishOutcome.PUBLISHED,
                platform="github",
                published_url=release_data.get("html_url"),
                message=(
                    None
                    if release_data.get("html_url")
                    else "GitHub accepted the release but did not return its URL."
                ),
            )
