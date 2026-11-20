"""Multi-platform social router with retry backoff and rate limit handling."""

import os
import random
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import httpx

from lore.core.database import Database
from lore.core.models import Draft, DraftStatus, LoreConfig, Platform, PublishQueueItem
from lore.publishing.base import PublishResult
from lore.publishing.bluesky import BlueskyPublisher
from lore.publishing.github_release import GitHubReleasePublisher
from lore.publishing.linkedin import LinkedInPublisher
from lore.publishing.twitter_bridge import TwitterBridgePublisher


class SocialRouter:
    """Dispatches approved drafts to platforms with exponential backoff and rate-limit handling."""

    @classmethod
    def publish_draft(
        cls,
        draft_id: str,
        platform: Platform,
        db: Database,
        config: Optional[LoreConfig] = None,
    ) -> PublishResult:
        draft = db.get_draft(draft_id)
        if not draft:
            return PublishResult(success=False, platform=platform.value, error=f"Draft {draft_id} not found")

        content = draft.humanized_content
        image_path = draft.card_image_path

        try:
            if platform == Platform.LINKEDIN:
                res = LinkedInPublisher.publish(content=content, image_path=image_path)
            elif platform == Platform.BLUESKY:
                res = BlueskyPublisher.publish(content=content, image_path=image_path)
            elif platform == Platform.TWITTER:
                res = TwitterBridgePublisher.publish(content=content, image_path=image_path)
            elif platform == Platform.GITHUB or platform == Platform.CHANGELOG:
                res = GitHubReleasePublisher.publish(draft=draft)
            else:
                # Default clipboard fallback
                res = TwitterBridgePublisher.publish(content=content, image_path=image_path)

            if res.success:
                db.update_draft_status(draft_id, DraftStatus.PUBLISHED, published_url=res.published_url)
            else:
                cls._handle_failure(db, draft_id, platform.value, res)

            return res

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 429:
                retry_after = int(e.response.headers.get("Retry-After", "60"))
                res = PublishResult(
                    success=False,
                    platform=platform.value,
                    error=f"Rate limited (429). Retry after {retry_after}s",
                    retry_after_seconds=retry_after,
                )
                cls._handle_failure(db, draft_id, platform.value, res)
                return res
            elif status_code in [400, 401, 403]:
                res = PublishResult(
                    success=False,
                    platform=platform.value,
                    error=f"Client error ({status_code}): {e.response.text[:200]}",
                )
                cls._handle_failure(db, draft_id, platform.value, res, permanent=True)
                return res
            else:
                res = PublishResult(
                    success=False,
                    platform=platform.value,
                    error=f"Server error ({status_code}): {e.response.text[:200]}",
                )
                cls._handle_failure(db, draft_id, platform.value, res)
                return res
        except Exception as e:
            res = PublishResult(success=False, platform=platform.value, error=str(e))
            cls._handle_failure(db, draft_id, platform.value, res)
            return res

    @classmethod
    def _handle_failure(
        cls,
        db: Database,
        draft_id: str,
        platform_str: str,
        res: PublishResult,
        permanent: bool = False,
    ) -> None:
        import random
        now = datetime.now(timezone.utc)
        base_delay = res.retry_after_seconds or 30
        jitter = random.uniform(0.85, 1.15)
        retry_delay = int(base_delay * jitter)
        scheduled_retry = now + timedelta(seconds=retry_delay)

        queue_item = PublishQueueItem(
            id=f"pub_{draft_id}_{platform_str}",
            draft_id=draft_id,
            platform=Platform(platform_str) if platform_str in [p.value for p in Platform] else Platform.TWITTER,
            scheduled_time=scheduled_retry,
            attempts=1,
            last_error=res.error[:300] if res.error else None,
            status="failed" if permanent else "pending",
        )
        db.enqueue_publish(queue_item)
