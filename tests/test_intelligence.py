"""Tests for Angle Finder and Content Calendar."""

from datetime import datetime, timezone
import pytest

from lore.core.models import AtomType, ContentAtom, EvidenceRecord, Platform
from lore.intelligence.angle_finder import AngleFinder
from lore.intelligence.calendar import ContentCalendar


@pytest.fixture
def sample_feature_atom():
    return ContentAtom(
        id="atom_feat_1",
        project_id="proj_x",
        atom_type=AtomType.FEATURE,
        title="WebSockets Live Sync",
        summary="Added real-time sync with 400 lines of python",
        evidence=EvidenceRecord(
            commits=["1111"],
            files_changed=4,
            insertions=350,
            deletions=10,
            key_files=["sync.py", "server.py"],
        ),
        tech_stack=["Python", "FastAPI", "WebSockets"],
        potential_score=0.88,
    )


@pytest.fixture
def sample_bugfix_atom():
    return ContentAtom(
        id="atom_fix_1",
        project_id="proj_x",
        atom_type=AtomType.BUGFIX,
        title="Redis Memory Spike Fix",
        summary="Fixed unbounded key creation",
        evidence=EvidenceRecord(
            commits=["2222"],
            files_changed=2,
            insertions=12,
            deletions=8,
            key_files=["cache.py"],
        ),
        tech_stack=["Redis", "Python"],
        potential_score=0.75,
    )


def test_angle_finder_for_feature(sample_feature_atom):
    angles = AngleFinder.find_angles(sample_feature_atom)
    assert len(angles) >= 3

    angle_names = [a.name for a in angles]
    assert "Problem-Solution" in angle_names
    assert "Technical Deep Dive" in angle_names
    assert "The Trade-off" in angle_names

    deep_dive = next(a for a in angles if a.name == "Technical Deep Dive")
    assert Platform.THREAD in deep_dive.best_platforms
    assert "WebSockets Live Sync" in deep_dive.hook


def test_angle_finder_for_bugfix(sample_bugfix_atom):
    angles = AngleFinder.find_angles(sample_bugfix_atom)
    assert len(angles) >= 2

    war_story = next(a for a in angles if a.name == "The War Story")
    assert "subtle bug" in war_story.hook.lower()
    assert Platform.TWITTER in war_story.best_platforms


def test_content_calendar_planning(sample_feature_atom, sample_bugfix_atom):
    atoms = [sample_feature_atom, sample_bugfix_atom]
    start = datetime(2026, 11, 23, tzinfo=timezone.utc)  # A Monday

    schedule = ContentCalendar.plan_week(atoms, start_date=start)
    assert len(schedule) == 5

    # Check platforms match the cadence
    assert schedule[0].platform == Platform.LINKEDIN
    assert schedule[1].platform == Platform.TWITTER
    assert schedule[2].platform == Platform.THREAD
    assert schedule[3].platform == Platform.LINKEDIN
    assert schedule[4].platform == Platform.TWITTER

    # Check that each slot has an angle and hook
    for slot in schedule:
        assert slot.suggested_hook != ""
        assert slot.angle_name != ""
        assert slot.day_of_week in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
