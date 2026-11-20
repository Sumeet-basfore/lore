"""Tests for Multi-Platform Publishing Engine."""

import pytest
from lore.core.database import Database
from lore.core.models import Draft, DraftStatus, Platform
from lore.publishing.bluesky import compute_byte_facets
from lore.publishing.linkedin import format_linkedin_monospace
from lore.publishing.social_router import SocialRouter


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


def test_social_router_mock_mode(tmp_path):
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
    )
    db.save_draft(draft)

    res = SocialRouter.publish_draft("d_pub_1", Platform.LINKEDIN, db=db)
    assert res.success is True
    assert "linkedin.com" in res.published_url

    updated = db.get_draft("d_pub_1")
    assert updated.status == DraftStatus.PUBLISHED
