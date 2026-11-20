"""Unit tests for Lore Core (Config, Models, Database)."""

import tempfile
from datetime import datetime, timezone
from pathlib import Path
import pytest

from lore.config import LoreConfig, load_config, save_config, update_config
from lore.core.database import Database
from lore.core.models import (
    AtomType,
    ContentAtom,
    Draft,
    DraftStatus,
    EvidenceRecord,
    Platform,
    Project,
    VoiceSample,
)


@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        db = Database(db_path=Path(f.name))
        yield db


def test_config_save_and_load(tmp_path, monkeypatch):
    monkeypatch.setenv("LORE_HOME", str(tmp_path))
    cfg = LoreConfig(
        llm_provider="ollama",
        llm_model="llama3.2:3b",
        author_name="Alice",
    )
    save_config(cfg)

    loaded = load_config()
    assert loaded.llm_provider == "ollama"
    assert loaded.llm_model == "llama3.2:3b"
    assert loaded.author_name == "Alice"

    updated = update_config({"author_handle": "@alicetech"})
    assert updated.author_handle == "@alicetech"


def test_database_project_crud(temp_db):
    proj = Project(
        id="proj_1",
        name="Veltr",
        path="/tmp/veltr",
        description="Personal OS",
        tech_stack=["Python", "FastAPI", "Next.js"],
    )
    temp_db.add_project(proj)

    fetched = temp_db.get_project("proj_1")
    assert fetched is not None
    assert fetched.name == "Veltr"
    assert "FastAPI" in fetched.tech_stack

    by_name = temp_db.get_project("Veltr")
    assert by_name is not None
    assert by_name.id == "proj_1"

    projects = temp_db.list_projects()
    assert len(projects) == 1

    temp_db.update_project_scan_time("proj_1", datetime.now(timezone.utc))
    updated_proj = temp_db.get_project("proj_1")
    assert updated_proj.last_scanned_at is not None

    removed = temp_db.remove_project("proj_1")
    assert removed is True
    assert temp_db.get_project("proj_1") is None


def test_database_atom_and_draft_crud(temp_db):
    proj = Project(id="p1", name="App", path="/tmp/app")
    temp_db.add_project(proj)

    evidence = EvidenceRecord(
        commits=["a1b2c3d"],
        files_changed=3,
        insertions=120,
        deletions=10,
        key_files=["server.py"],
        sample_messages=["feat: add websocket sync"],
    )
    atom = ContentAtom(
        id="atom_1",
        project_id="p1",
        atom_type=AtomType.FEATURE,
        title="WebSocket Sync",
        summary="Added real-time WebSocket sync",
        evidence=evidence,
        tech_stack=["Python", "WebSocket"],
        potential_score=0.85,
    )
    temp_db.save_atom(atom)

    fetched_atom = temp_db.get_atom("atom_1")
    assert fetched_atom is not None
    assert fetched_atom.evidence.insertions == 120
    assert fetched_atom.atom_type == AtomType.FEATURE

    draft = Draft(
        id="draft_1",
        atom_id="atom_1",
        project_id="p1",
        platform=Platform.TWITTER,
        title="Real-time sync post",
        raw_content="Excited to announce real-time sync!",
        humanized_content="We shipped real-time sync with WebSockets today.",
        humanizer_audit={"tells_removed": ["excited to announce"]},
        status=DraftStatus.DRAFTED,
    )
    temp_db.save_draft(draft)

    fetched_draft = temp_db.get_draft("draft_1")
    assert fetched_draft is not None
    assert fetched_draft.humanized_content.startswith("We shipped")

    temp_db.update_draft_status("draft_1", DraftStatus.APPROVED)
    approved_drafts = temp_db.list_drafts(status=DraftStatus.APPROVED)
    assert len(approved_drafts) == 1
    assert approved_drafts[0].id == "draft_1"


def test_voice_sample_crud(temp_db):
    sample = VoiceSample(
        id="v1",
        title="Launch Tweet Sample",
        content="Shipped a quick update. Saved 4 hours of debugging.",
        analysis={"avg_sentence_len": 6.5},
    )
    temp_db.save_voice_sample(sample)

    samples = temp_db.list_voice_samples()
    assert len(samples) == 1
    assert samples[0].title == "Launch Tweet Sample"

    temp_db.delete_voice_sample("v1")
    assert len(temp_db.list_voice_samples()) == 0
