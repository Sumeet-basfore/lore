"""Tests for Content Atom extraction and evidence ledger."""

from datetime import datetime, timezone
import pytest

from lore.core.models import AtomType, GitCommit
from lore.extraction.atom_extractor import AtomExtractor
from lore.extraction.evidence import build_evidence_from_commits


def make_commit(sha: str, summary: str, files=None, ins=10, dels=2):
    return GitCommit(
        sha=sha,
        short_sha=sha[:7],
        author="Sumeet",
        email="sumeet@example.com",
        timestamp=datetime.now(timezone.utc),
        message=summary,
        summary=summary,
        files_changed=files or ["src/api.py"],
        insertions=ins,
        deletions=dels,
    )


def test_build_evidence():
    c1 = make_commit("11111111", "feat(api): endpoint", ["src/api.py", "src/models.py"], 50, 5)
    c2 = make_commit("22222222", "feat(api): tests", ["tests/test_api.py"], 30, 2)

    evidence = build_evidence_from_commits([c1, c2])
    assert evidence.files_changed == 3
    assert evidence.insertions == 80
    assert evidence.deletions == 7
    assert len(evidence.commits) == 2
    assert "src/api.py" in evidence.key_files


def test_atom_extractor_clustering():
    commits = [
        make_commit("aaaa1111", "feat(auth): add JWT login", ["src/auth.py"], 120, 10),
        make_commit("aaaa2222", "feat(auth): add refresh token", ["src/auth.py", "src/tokens.py"], 60, 5),
        make_commit("bbbb1111", "fix(cache): resolve Redis leak", ["src/cache.py"], 15, 20),
        make_commit("cccc1111", "refactor(db): migrate to async connection pool", ["src/db.py"], 80, 70),
    ]

    tags = [{"name": "v1.2.0", "sha": "aaaa2222"}]
    tech_stack = ["Python", "FastAPI", "Redis"]

    atoms = AtomExtractor.extract_atoms(
        project_id="proj_test",
        commits=commits,
        tags=tags,
        tech_stack=tech_stack,
    )

    assert len(atoms) >= 4

    # Top atom should be high scoring (Release milestone or Auth feature)
    atom_types = [a.atom_type for a in atoms]
    assert AtomType.MILESTONE in atom_types
    assert AtomType.FEATURE in atom_types
    assert AtomType.BUGFIX in atom_types
    assert AtomType.REFACTOR in atom_types

    # Find the auth feature atom
    auth_atom = next(a for a in atoms if "JWT" in a.title or "Auth" in a.title or "add JWT" in a.summary)
    assert auth_atom.evidence.files_changed == 2
    assert auth_atom.evidence.insertions == 180
    assert len(auth_atom.evidence.commits) == 2
    assert auth_atom.potential_score >= 0.7
