"""Tests for Approval Gateways (Local Web Server, Slack, Discord, Telegram)."""

import json
from pathlib import Path
import tempfile
import urllib.request
import pytest

from lore.approval.discord_gateway import build_discord_payload
from lore.approval.local_web import LoreWebReviewServer
from lore.approval.slack_gateway import build_slack_blocks
from lore.approval.telegram_gateway import build_telegram_payload
from lore.core.database import Database
from lore.core.models import Draft, DraftStatus, Platform, Project


@pytest.fixture
def test_db():
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        db = Database(db_path=Path(f.name))
        db.add_project(Project(id="proj_test", name="Test Project", path="/tmp"))
        draft = Draft(
            id="draft_review_1",
            project_id="proj_test",
            platform=Platform.TWITTER,
            title="FastAPI Async Engine",
            raw_content="Raw draft text",
            humanized_content="Shipped async engine for FastAPI.",
            status=DraftStatus.DRAFTED,
        )
        db.save_draft(draft)
        yield db


def test_slack_block_kit_schema(test_db):
    draft = test_db.get_draft("draft_review_1")
    blocks = build_slack_blocks(draft, card_image_url="https://lore.dev/card.png")

    assert len(blocks) >= 4
    assert blocks[0]["type"] == "header"
    assert "FastAPI Async Engine" in blocks[0]["text"]["text"]
    assert blocks[-1]["type"] == "actions"


def test_discord_payload_schema(test_db):
    draft = test_db.get_draft("draft_review_1")
    payload = build_discord_payload(draft, card_image_url="https://lore.dev/card.png")

    assert "embeds" in payload
    embed = payload["embeds"][0]
    assert "FastAPI Async Engine" in embed["title"]
    assert embed["image"]["url"] == "https://lore.dev/card.png"


def test_telegram_payload_schema(test_db):
    draft = test_db.get_draft("draft_review_1")
    payload = build_telegram_payload("123456", draft)

    assert payload["chat_id"] == "123456"
    assert "FastAPI Async Engine" in payload["text"]
    assert "reply_markup" in payload


def test_local_web_server_lifecycle_and_api(test_db):
    server = LoreWebReviewServer(start_port=4750, max_attempts=5, db=test_db)
    url, port = server.start()

    try:
        # 1. Unauthenticated request should be forbidden
        unauth_req = urllib.request.Request(f"http://127.0.0.1:{port}/")
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(unauth_req)
        assert exc_info.value.code == 403

        # 2. Authenticated GET /
        with urllib.request.urlopen(url) as resp:
            assert resp.status == 200
            html = resp.read().decode("utf-8")
            assert "Lore Review Gateway" in html

        # 3. Authenticated GET /api/drafts
        drafts_url = f"http://127.0.0.1:{port}/api/drafts?token={server.session_token}"
        with urllib.request.urlopen(drafts_url) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert len(data) == 1
            assert data[0]["id"] == "draft_review_1"

        # 4. Authenticated POST /api/drafts/<id>/approve
        approve_url = f"http://127.0.0.1:{port}/api/drafts/draft_review_1/approve?token={server.session_token}"
        post_req = urllib.request.Request(approve_url, data=b"", method="POST")
        with urllib.request.urlopen(post_req) as resp:
            assert resp.status == 200
            result = json.loads(resp.read().decode("utf-8"))
            assert result["status"] == "approved"

        # Verify DB updated
        updated_draft = test_db.get_draft("draft_review_1")
        assert updated_draft.status == DraftStatus.APPROVED
    finally:
        server.stop()


def test_card_path_traversal_sandboxing(test_db):
    server = LoreWebReviewServer(start_port=4753, db=test_db)
    url_str, port = server.start()
    try:
        draft = test_db.get_draft("draft_review_1")
        # Attempt arbitrary file path traversal
        draft.card_image_path = "/etc/passwd"
        test_db.save_draft(draft)

        url = f"http://127.0.0.1:{port}/api/drafts/draft_review_1/card?token={server.session_token}"
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(url)
        assert exc_info.value.code == 403
    finally:
        server.stop()


def test_gateway_ssrf_prevention(test_db):
    from lore.approval.slack_gateway import send_slack_approval_card
    from lore.approval.discord_gateway import send_discord_approval_card

    draft = test_db.get_draft("draft_review_1")
    # SSRF attempts to AWS metadata and internal services
    assert send_slack_approval_card("http://169.254.169.254/latest/meta-data/", draft) is False
    assert send_slack_approval_card("http://127.0.0.1:8000/internal", draft) is False
    assert send_discord_approval_card("http://169.254.169.254/latest/meta-data/", draft) is False
