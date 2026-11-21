"""Tests for resolving the current Git repository to a Lore project."""

import subprocess
from pathlib import Path

from lore.core.database import Database
from lore.core.models import Project
from lore.project_context import find_git_root


def run_git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def make_repo(repo: Path) -> None:
    repo.mkdir(parents=True)
    run_git(repo, "init")
    run_git(repo, "config", "user.name", "Test User")
    run_git(repo, "config", "user.email", "test@example.com")
    (repo / "README.md").write_text("# Test repo\n", encoding="utf-8")
    run_git(repo, "add", "README.md")
    run_git(repo, "commit", "-m", "Add test README")


def test_find_git_root_from_nested_directory(tmp_path):
    repo = tmp_path / "repo with spaces"
    nested = repo / "src" / "package"
    make_repo(repo)
    nested.mkdir(parents=True)

    assert find_git_root(nested) == repo.resolve()


def test_find_git_root_supports_worktree_git_file(tmp_path):
    repo = tmp_path / "main-repo"
    worktree = tmp_path / "worktree with spaces"
    make_repo(repo)
    run_git(repo, "worktree", "add", "-b", "feature", str(worktree))
    nested = worktree / "src"
    nested.mkdir()

    assert (worktree / ".git").is_file()
    assert find_git_root(nested) == worktree.resolve()


def test_find_git_root_returns_none_outside_git_repo(tmp_path):
    assert find_git_root(tmp_path) is None


def test_database_project_lookup_normalizes_path(tmp_path):
    repo = tmp_path / "project with spaces"
    repo.mkdir()
    temp_db = Database(tmp_path / "lore.db")
    project = Project(id="proj_spaces", name="Spaces", path=str(repo.resolve()))
    temp_db.add_project(project)

    noncanonical_path = repo.parent / "unused" / ".." / repo.name
    assert temp_db.get_project_by_path(noncanonical_path) == project
