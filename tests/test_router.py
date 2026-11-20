"""Tests for LLM Router and Jinja2 Prompt Templates."""

import pytest

from lore.core.models import AtomType, ContentAtom, EvidenceRecord, LoreConfig, Platform
from lore.generation.router import LLMRouter
from lore.intelligence.angle_finder import StoryAngle


@pytest.fixture
def sample_atom():
    return ContentAtom(
        id="atom_123",
        project_id="test_project",
        atom_type=AtomType.FEATURE,
        title="WebSocket Sync Engine",
        summary="Replaced polling with WebSockets",
        evidence=EvidenceRecord(
            commits=["sha1", "sha2"],
            files_changed=4,
            insertions=350,
            deletions=20,
            key_files=["sync.py", "server.py"],
            sample_messages=["feat: add websocket channel"],
        ),
        tech_stack=["Python", "FastAPI", "WebSockets"],
        potential_score=0.9,
    )


def test_render_twitter_prompt(sample_atom):
    router = LLMRouter(LoreConfig())
    angle = StoryAngle(
        name="Problem-Solution",
        hook="We replaced polling with WebSockets today.",
        narrative_arc="Problem -> Fix -> Result",
        best_platforms=[Platform.TWITTER],
        rationale="Clear and direct.",
    )
    prompt = router.render_prompt(
        platform=Platform.TWITTER,
        project_name="SyncEngine",
        atom=sample_atom,
        angle=angle,
    )

    assert "PROJECT: SyncEngine" in prompt
    assert "WebSocket Sync Engine" in prompt
    assert "Strictly under 280 characters" in prompt
    assert "NO AI BUZZWORDS" in prompt


def test_render_thread_prompt(sample_atom):
    router = LLMRouter(LoreConfig())
    prompt = router.render_prompt(
        platform=Platform.THREAD,
        project_name="SyncEngine",
        atom=sample_atom,
    )
    assert "Twitter thread (3 to 6 tweets)" in prompt
    assert 'separated by "---"' in prompt


def test_render_linkedin_prompt(sample_atom):
    router = LLMRouter(LoreConfig())
    prompt = router.render_prompt(
        platform=Platform.LINKEDIN,
        project_name="SyncEngine",
        atom=sample_atom,
    )
    assert "800 to 1,200 characters" in prompt
    assert "NO CORPORATE AI SLOP" in prompt


def test_mock_generation(sample_atom):
    router = LLMRouter(LoreConfig())
    prompt = router.render_prompt(
        platform=Platform.TWITTER,
        project_name="SyncEngine",
        atom=sample_atom,
    )
    output = router.generate(prompt, force_mock=True)
    assert "Shipped real-time sync" in output
    assert len(output) < 280
