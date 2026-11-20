"""Tests for Multi-Platform Publishing Engine."""

from datetime import datetime, timedelta, timezone
from email.utils import format_datetime, parsedate_to_datetime

import httpx
import pytest
from lore.core.database import Database
from lore.core.models import Draft, DraftStatus, Platform
from lore.publishing.base import PublishOutcome, PublishResult
from lore.publishing.bluesky import BlueskyPublisher, compute_byte_facets
from lore.publishing.github_release import GitHubReleasePublisher
from lore.publishing.linkedin import LinkedInPublisher, format_linkedin_monospace
from lore.publishing.social_router import SocialRouter
from lore.publishing.twitter_bridge import TwitterBridgePublisher


def test_linkedin_monospace_formatter():
    text = "We switched to `SQLite` and `FastAPI`."
    res = format_linkedin_monospace(text)
    assert "`" not in res
    assert "SQLite" not in res  # Replaced with unicode monospace math characters


def test_bluesky_utf8_byte_facets():
    text = "Check out our repo https://github.com/example/lore and ping @alice!"
    facets = compute_byte_facets(text)
    assert len(facets) == 2

    # Verify byte offsets align with the encoded string
    text_bytes = text.encode("utf-8")
    for f in facets:
        start = f["index"]["byteStart"]
        end = f["index"]["byteEnd"]
        token_bytes = text_bytes[start:end]
        assert token_bytes.startswith(b"http") or token_bytes.startswith(b"@")


def _make_draft(tmp_path, status=DraftStatus.APPROVED):
    from lore.core.models import Project

    db = Database(db_path=tmp_path / "test.db")
    project = Project(id="p1", name="Project 1", path=str(tmp_path))
    db.add_project(project)
    draft = Draft(
        id="d_pub_1",
        project_id="p1",
        platform=Platform.LINKEDIN,
        title="Architecture Update",
        raw_content="Shipped new DB.",
        humanized_content="Shipped new DB.",
        status=status,
    )
    db.save_draft(draft)
    return db, draft


class _FakeResponse:
    def __init__(self, payload=None, headers=None):
        self._payload = payload or {}
        self.headers = headers or {}

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeClient:
    def __init__(self, responses):
        self._responses = iter(responses)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def post(self, *_args, **_kwargs):
        return next(self._responses)


def _raise_http_status(status_code, headers=None):
    def publish(**_kwargs):
        response = httpx.Response(
            status_code,
            headers=headers,
            content=b"provider response",
            request=httpx.Request("POST", "https://provider.example/posts"),
        )
        response.raise_for_status()

    return publish


@pytest.mark.parametrize("publisher", ["linkedin", "bluesky", "github"])
def test_missing_credentials_fail_without_published_url(tmp_path, monkeypatch, publisher):
    for key in (
        "LINKEDIN_ACCESS_TOKEN",
        "LINKEDIN_AUTHOR_URN",
        "BLUESKY_HANDLE",
        "BLUESKY_APP_PASSWORD",
        "GITHUB_TOKEN",
        "GITHUB_REPOSITORY",
        "LORE_MOCK_PUBLISHING",
        "LORE_MOCK_LLM",
    ):
        monkeypatch.delenv(key, raising=False)

    _, draft = _make_draft(tmp_path)
    results = {
        "linkedin": LinkedInPublisher.publish("Shipped new DB."),
        "bluesky": BlueskyPublisher.publish("Shipped new DB."),
        "github": GitHubReleasePublisher.publish(draft),
    }

    result = results[publisher]
    assert result.success is False
    assert result.outcome == PublishOutcome.FAILED
    assert result.published_url is None
    assert result.retryable is False


def test_model_mock_mode_does_not_mock_publishing(monkeypatch):
    monkeypatch.setenv("LORE_MOCK_LLM", "1")
    monkeypatch.delenv("LORE_MOCK_PUBLISHING", raising=False)
    monkeypatch.delenv("LINKEDIN_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("LINKEDIN_AUTHOR_URN", raising=False)

    result = LinkedInPublisher.publish("Shipped new DB.")

    assert result.success is False
    assert result.outcome == PublishOutcome.FAILED
    assert result.published_url is None


def test_explicit_publish_simulation_has_no_published_urls(tmp_path, monkeypatch):
    monkeypatch.setenv("LORE_MOCK_PUBLISHING", "1")
    monkeypatch.delenv("LORE_MOCK_LLM", raising=False)
    _, draft = _make_draft(tmp_path)

    results = [
        LinkedInPublisher.publish("Shipped new DB."),
        BlueskyPublisher.publish("Shipped new DB."),
        GitHubReleasePublisher.publish(draft),
    ]

    assert all(result.success for result in results)
    assert all(result.outcome == PublishOutcome.SIMULATED for result in results)
    assert all(result.published_url is None for result in results)


def test_explicit_publish_simulation_is_not_recorded_as_published(tmp_path, monkeypatch):
    monkeypatch.setenv("LORE_MOCK_PUBLISHING", "1")
    db, draft = _make_draft(tmp_path)

    result = SocialRouter.publish_draft(draft.id, Platform.LINKEDIN, db=db)

    assert result.success is True
    assert result.outcome == PublishOutcome.SIMULATED
    assert result.published_url is None
    assert db.get_draft(draft.id).status == DraftStatus.APPROVED
    assert db.get_pending_publishes() == []


def test_nonretryable_failure_does_not_enter_retry_queue(tmp_path, monkeypatch):
    db, draft = _make_draft(tmp_path)
    monkeypatch.setattr(
        LinkedInPublisher,
        "publish",
        lambda **kwargs: PublishResult(
            success=False,
            outcome=PublishOutcome.FAILED,
            platform="linkedin",
            error="Missing credentials.",
        ),
    )

    result = SocialRouter.publish_draft(draft.id, Platform.LINKEDIN, db=db)

    assert result.outcome == PublishOutcome.FAILED
    assert db.get_draft(draft.id).status == DraftStatus.APPROVED
    assert db.get_pending_publishes() == []


def test_retryable_failure_enters_retry_queue(tmp_path, monkeypatch):
    db, draft = _make_draft(tmp_path)
    monkeypatch.setattr(
        LinkedInPublisher,
        "publish",
        lambda **kwargs: PublishResult(
            success=False,
            outcome=PublishOutcome.FAILED,
            platform="linkedin",
            error="Temporary network failure.",
            retryable=True,
        ),
    )

    result = SocialRouter.publish_draft(draft.id, Platform.LINKEDIN, db=db)

    queued = db.get_pending_publishes()
    assert result.outcome == PublishOutcome.FAILED
    assert len(queued) == 1
    assert queued[0].draft_id == draft.id


@pytest.mark.parametrize("status_code", [409, 422])
def test_http_validation_errors_are_not_retried(tmp_path, monkeypatch, status_code):
    db, draft = _make_draft(tmp_path)
    monkeypatch.setattr(LinkedInPublisher, "publish", _raise_http_status(status_code))

    result = SocialRouter.publish_draft(draft.id, Platform.LINKEDIN, db=db)

    assert result.outcome == PublishOutcome.FAILED
    assert result.retryable is False
    assert db.get_pending_publishes() == []


@pytest.mark.parametrize("status_code", [500, 503])
def test_http_server_errors_are_retried(tmp_path, monkeypatch, status_code):
    db, draft = _make_draft(tmp_path)
    monkeypatch.setattr(LinkedInPublisher, "publish", _raise_http_status(status_code))

    result = SocialRouter.publish_draft(draft.id, Platform.LINKEDIN, db=db)

    assert result.outcome == PublishOutcome.FAILED
    assert result.retryable is True
    assert len(db.get_pending_publishes()) == 1


def test_http_request_timeout_is_retried(tmp_path, monkeypatch):
    db, draft = _make_draft(tmp_path)
    monkeypatch.setattr(LinkedInPublisher, "publish", _raise_http_status(408))

    result = SocialRouter.publish_draft(draft.id, Platform.LINKEDIN, db=db)

    assert result.retryable is True
    assert result.retry_after_seconds == 60
    assert len(db.get_pending_publishes()) == 1


def test_retry_after_delta_seconds_is_used(tmp_path, monkeypatch):
    db, draft = _make_draft(tmp_path)
    before_publish = datetime.now(timezone.utc)
    monkeypatch.setattr(
        LinkedInPublisher,
        "publish",
        _raise_http_status(429, {"Retry-After": "120"}),
    )

    result = SocialRouter.publish_draft(draft.id, Platform.LINKEDIN, db=db)

    assert result.retryable is True
    assert result.retry_after_seconds == 120
    assert len(db.get_pending_publishes()) == 1
    assert db.get_pending_publishes()[0].scheduled_time >= before_publish + timedelta(seconds=120)


def test_retry_after_http_date_is_parsed(tmp_path, monkeypatch):
    db, draft = _make_draft(tmp_path)
    future = datetime.now(timezone.utc) + timedelta(seconds=120)
    retry_after = format_datetime(future, usegmt=True)
    retry_deadline = parsedate_to_datetime(retry_after)
    monkeypatch.setattr(
        LinkedInPublisher,
        "publish",
        _raise_http_status(429, {"Retry-After": retry_after}),
    )

    result = SocialRouter.publish_draft(draft.id, Platform.LINKEDIN, db=db)

    assert result.retryable is True
    assert result.retry_after_seconds is not None
    assert 100 <= result.retry_after_seconds <= 120
    assert len(db.get_pending_publishes()) == 1
    assert db.get_pending_publishes()[0].scheduled_time >= retry_deadline


@pytest.mark.parametrize("retry_after", ["not-a-date", "31622401", "9" * 5000])
def test_invalid_or_oversized_retry_after_uses_safe_default(tmp_path, monkeypatch, retry_after):
    db, draft = _make_draft(tmp_path)
    monkeypatch.setattr(
        LinkedInPublisher,
        "publish",
        _raise_http_status(429, {"Retry-After": retry_after}),
    )

    result = SocialRouter.publish_draft(draft.id, Platform.LINKEDIN, db=db)

    assert result.retryable is True
    assert result.retry_after_seconds == 60
    assert len(db.get_pending_publishes()) == 1


def test_twitter_intent_is_a_handoff_not_a_published_post(tmp_path, monkeypatch):
    db, draft = _make_draft(tmp_path)

    result = SocialRouter.publish_draft(draft.id, Platform.TWITTER, db=db)

    assert result.success is True
    assert result.outcome == PublishOutcome.HANDOFF
    assert result.action_url.startswith("https://twitter.com/intent/tweet?")
    assert result.published_url is None
    assert db.get_draft(draft.id).status == DraftStatus.APPROVED


def test_unapproved_draft_cannot_be_published(tmp_path, monkeypatch):
    db, draft = _make_draft(tmp_path, status=DraftStatus.DRAFTED)
    monkeypatch.setattr(
        LinkedInPublisher,
        "publish",
        lambda **kwargs: pytest.fail("publisher must not run before approval"),
    )

    result = SocialRouter.publish_draft(draft.id, Platform.LINKEDIN, db=db)

    assert result.success is False
    assert result.outcome == PublishOutcome.FAILED
    assert db.get_draft(draft.id).status == DraftStatus.DRAFTED


def test_unsupported_platform_does_not_fall_back_to_twitter(tmp_path, monkeypatch):
    db, draft = _make_draft(tmp_path)
    monkeypatch.setattr(
        TwitterBridgePublisher,
        "publish",
        lambda **kwargs: pytest.fail("unsupported platforms must not open a Twitter hand-off"),
    )

    result = SocialRouter.publish_draft(draft.id, Platform.BLOG, db=db)

    assert result.success is False
    assert result.outcome == PublishOutcome.FAILED
    assert result.published_url is None
    assert result.action_url is None
    assert db.get_draft(draft.id).status == DraftStatus.APPROVED


def test_confirmed_provider_result_marks_draft_published(tmp_path, monkeypatch):
    db, draft = _make_draft(tmp_path)
    monkeypatch.setattr(
        LinkedInPublisher,
        "publish",
        lambda **kwargs: PublishResult(
            success=True,
            outcome=PublishOutcome.PUBLISHED,
            platform="linkedin",
            published_url="https://www.linkedin.com/feed/update/urn:li:share:real123",
        ),
    )

    result = SocialRouter.publish_draft(draft.id, Platform.LINKEDIN, db=db)

    assert result.outcome == PublishOutcome.PUBLISHED
    assert db.get_draft(draft.id).status == DraftStatus.PUBLISHED
    assert db.get_draft(draft.id).published_url == result.published_url


@pytest.mark.parametrize(
    ("publisher", "env", "responses", "expected_url"),
    [
        (
            "linkedin",
            {"LINKEDIN_ACCESS_TOKEN": "test-token", "LINKEDIN_AUTHOR_URN": "urn:li:person:test"},
            [_FakeResponse(headers={"x-restli-id": "urn:li:share:real123"})],
            "https://www.linkedin.com/feed/update/urn:li:share:real123",
        ),
        (
            "bluesky",
            {"BLUESKY_HANDLE": "dev.example", "BLUESKY_APP_PASSWORD": "app-password"},
            [
                _FakeResponse({"accessJwt": "session-token", "did": "did:plc:dev"}),
                _FakeResponse({"uri": "at://did:plc:dev/app.bsky.feed.post/record123"}),
            ],
            "https://bsky.app/profile/dev.example/post/record123",
        ),
        (
            "github",
            {"GITHUB_TOKEN": "test-token", "GITHUB_REPOSITORY": "owner/repository"},
            [_FakeResponse({"html_url": "https://github.com/owner/repository/releases/tag/v2"})],
            "https://github.com/owner/repository/releases/tag/v2",
        ),
    ],
)
def test_provider_confirmation_returns_published_outcome(
    tmp_path, monkeypatch, publisher, env, responses, expected_url
):
    monkeypatch.delenv("LORE_MOCK_PUBLISHING", raising=False)
    monkeypatch.delenv("LORE_MOCK_LLM", raising=False)
    for key in (
        "LINKEDIN_ACCESS_TOKEN",
        "LINKEDIN_AUTHOR_URN",
        "BLUESKY_HANDLE",
        "BLUESKY_APP_PASSWORD",
        "GITHUB_TOKEN",
        "GITHUB_REPOSITORY",
    ):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)

    fake_client = lambda **_kwargs: _FakeClient(responses)
    if publisher == "linkedin":
        monkeypatch.setattr("lore.publishing.linkedin.httpx.Client", fake_client)
        result = LinkedInPublisher.publish("Shipped new DB.")
    elif publisher == "bluesky":
        monkeypatch.setattr("lore.publishing.bluesky.httpx.Client", fake_client)
        result = BlueskyPublisher.publish("Shipped new DB.")
    else:
        monkeypatch.setattr("lore.publishing.github_release.httpx.Client", fake_client)
        _, draft = _make_draft(tmp_path)
        result = GitHubReleasePublisher.publish(draft)

    assert result.success is True
    assert result.outcome == PublishOutcome.PUBLISHED
    assert result.published_url == expected_url
