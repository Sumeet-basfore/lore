"""Multi-platform social router with retry backoff and rate limit handling."""

import random
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from math import ceil
from typing import Optional
import httpx

from lore.core.database import Database
from lore.core.models import DraftStatus, LoreConfig, Platform, PublishQueueItem
from lore.publishing.base import PublishOutcome, PublishResult
from lore.publishing.bluesky import BlueskyPublisher
from lore.publishing.github_release import GitHubReleasePublisher
from lore.publishing.linkedin import LinkedInPublisher
from lore.publishing.twitter_bridge import TwitterBridgePublisher


DEFAULT_RETRY_AFTER_SECONDS = 60
MAX_RETRY_AFTER_SECONDS = 365 * 24 * 60 * 60


def _parse_retry_after(value: Optional[str]) -> int:
    """Parse Retry-After seconds or HTTP date, using a safe delay if invalid."""
    if value and value.isascii() and value.isdigit():
        try:
            delay = int(value)
        except (ValueError, OverflowError):
            return DEFAULT_RETRY_AFTER_SECONDS
        return delay if delay <= MAX_RETRY_AFTER_SECONDS else DEFAULT_RETRY_AFTER_SECONDS

    try:
        retry_at = parsedate_to_datetime(value or "")
    except (TypeError, ValueError, OverflowError):
        return DEFAULT_RETRY_AFTER_SECONDS

    if retry_at.tzinfo is None:
        retry_at = retry_at.replace(tzinfo=timezone.utc)
    delay = (retry_at.astimezone(timezone.utc) - datetime.now(timezone.utc)).total_seconds()
    if delay > MAX_RETRY_AFTER_SECONDS:
        return DEFAULT_RETRY_AFTER_SECONDS
    return max(0, ceil(delay))


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
            return PublishResult(
                success=False,
                outcome=PublishOutcome.FAILED,
                platform=platform.value,
                error=f"Draft {draft_id} not found.",
            )

        if draft.status != DraftStatus.APPROVED:
            return PublishResult(
                success=False,
                outcome=PublishOutcome.FAILED,
                platform=platform.value,
                error="Approve the draft before publishing it.",
            )

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
                return PublishResult(
                    success=False,
                    outcome=PublishOutcome.FAILED,
                    platform=platform.value,
                    error=f"Publishing to {platform.value} is not supported.",
                )

            if res.success and res.outcome == PublishOutcome.PUBLISHED:
                db.update_draft_status(draft_id, DraftStatus.PUBLISHED, published_url=res.published_url)
            elif res.outcome == PublishOutcome.FAILED and res.retryable:
                cls._handle_failure(db, draft_id, platform.value, res)

            return res

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code in (408, 429):
                retry_after = _parse_retry_after(e.response.headers.get("Retry-After"))
                res = PublishResult(
                    success=False,
                    outcome=PublishOutcome.FAILED,
                    platform=platform.value,
                    error=f"Transient client error ({status_code}). Retry after {retry_after}s",
                    retryable=True,
                    retry_after_seconds=retry_after,
                )
                cls._handle_failure(db, draft_id, platform.value, res)
                return res
            elif 400 <= status_code < 500:
                res = PublishResult(
                    success=False,
                    outcome=PublishOutcome.FAILED,
                    platform=platform.value,
                    error=f"Client error ({status_code}): {e.response.text[:200]}",
                )
                return res
            elif 500 <= status_code < 600:
                res = PublishResult(
                    success=False,
                    outcome=PublishOutcome.FAILED,
                    platform=platform.value,
                    error=f"Server error ({status_code}): {e.response.text[:200]}",
                    retryable=True,
                )
                cls._handle_failure(db, draft_id, platform.value, res)
                return res
            else:
                return PublishResult(
                    success=False,
                    outcome=PublishOutcome.FAILED,
                    platform=platform.value,
                    error=f"Unexpected HTTP status ({status_code}): {e.response.text[:200]}",
                )
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            res = PublishResult(
                success=False,
                outcome=PublishOutcome.FAILED,
                platform=platform.value,
                error=str(e),
                retryable=True,
            )
            cls._handle_failure(db, draft_id, platform.value, res)
            return res
        except Exception as e:
            return PublishResult(
                success=False,
                outcome=PublishOutcome.FAILED,
                platform=platform.value,
                error=str(e),
            )

    @classmethod
    def _handle_failure(
        cls,
        db: Database,
        draft_id: str,
        platform_str: str,
        res: PublishResult,
    ) -> None:
        now = datetime.now(timezone.utc)
        if res.retry_after_seconds is None:
            base_delay = 30
            jitter = random.uniform(0.85, 1.15)
        else:
            base_delay = res.retry_after_seconds
            jitter = random.uniform(1.0, 1.15)
        retry_delay = int(base_delay * jitter)
        scheduled_retry = now + timedelta(seconds=retry_delay)

        queue_item = PublishQueueItem(
            id=f"pub_{draft_id}_{platform_str}",
            draft_id=draft_id,
            platform=Platform(platform_str) if platform_str in [p.value for p in Platform] else Platform.TWITTER,
            scheduled_time=scheduled_retry,
            attempts=1,
            last_error=res.error[:300] if res.error else None,
            status="pending",
        )
        db.enqueue_publish(queue_item)
