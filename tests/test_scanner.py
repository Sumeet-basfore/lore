"""Tests for Git Scanner, Project Walker, and Filters."""

import subprocess
import tempfile
from pathlib import Path
import pytest

from lore.scanner.filters import is_noise_commit, is_noise_file, is_secret_file
from lore.scanner.git_scanner import GitScanner
from lore.scanner.project_walker import ProjectWalker


def test_filters():
    # Secret files
    assert is_secret_file(".env") is True
    assert is_secret_file(".env.local") is True
    assert is_secret_file("server.key") is True
    assert is_secret_file("id_rsa") is True
    assert is_secret_file("src/main.py") is False

    # Noise files
    assert is_noise_file("package-lock.json") is True
    assert is_noise_file("Cargo.lock") is True
    assert is_noise_file("bundle.min.js") is True
    assert is_noise_file("app.py") is False

    # Noise commits
    assert is_noise_commit("Merge branch 'main' of github.com") is True
    assert is_noise_commit("fix typo in readme") is True
    assert is_noise_commit("WIP: testing stuff") is True
    assert is_noise_commit("feat: add websocket real-time sync") is False


@pytest.fixture
def temp_git_repo():
    """Creates a temporary git repository with realistic commits for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_dir = Path(tmpdir)
        subprocess.run(["git", "init"], cwd=str(repo_dir), check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test Dev"], cwd=str(repo_dir), check=True)
        subprocess.run(["git", "config", "user.email", "dev@example.com"], cwd=str(repo_dir), check=True)

        # Commit 1: Feature
        feature_file = repo_dir / "sync.py"
        feature_file.write_text("def sync():\n    return 'synchronized'\n")
        subprocess.run(["git", "add", "sync.py"], cwd=str(repo_dir), check=True)
        subprocess.run(["git", "commit", "-m", "feat(sync): add real-time engine"], cwd=str(repo_dir), check=True)

        # Commit 2: Noise commit (typo)
        readme = repo_dir / "README.md"
        readme.write_text("# Sync Engine\n> High performance sync\n")
        subprocess.run(["git", "add", "README.md"], cwd=str(repo_dir), check=True)
        subprocess.run(["git", "commit", "-m", "fix typo in doc"], cwd=str(repo_dir), check=True)

        # Commit 3: Secret file (should be ignored by scanner)
        secret_file = repo_dir / ".env"
        secret_file.write_text("SECRET_KEY=12345\n")
        code_file = repo_dir / "auth.py"
        code_file.write_text("def authenticate():\n    return True\n")
        subprocess.run(["git", "add", ".env", "auth.py"], cwd=str(repo_dir), check=True)
        subprocess.run(["git", "commit", "-m", "feat(auth): add auth layer"], cwd=str(repo_dir), check=True)

        # Add tag
        subprocess.run(["git", "tag", "v1.0.0"], cwd=str(repo_dir), check=True)

        yield repo_dir


def test_git_scanner(temp_git_repo):
    scanner = GitScanner(temp_git_repo)
    commits = scanner.scan_commits()

    # Noise commit ("fix typo") was filtered out
    # Secret file (".env") was excluded from files_changed
    assert len(commits) == 2

    # Most recent commit is feat(auth)
    auth_commit = commits[0]
    assert "feat(auth)" in auth_commit.summary
    assert ".env" not in auth_commit.files_changed
    assert "auth.py" in auth_commit.files_changed

    # First commit is feat(sync)
    sync_commit = commits[1]
    assert "feat(sync)" in sync_commit.summary
    assert "sync.py" in sync_commit.files_changed
    assert sync_commit.insertions > 0

    # Tag discovery
    tags = scanner.get_tags()
    assert len(tags) == 1
    assert tags[0]["name"] == "v1.0.0"

    # Summary stats
    stats = scanner.get_summary_stats()
    assert stats["total_commits"] == 2
    assert "auth.py" in stats["unique_files"]


def test_project_walker(temp_git_repo):
    # Add a package.json and pyproject.toml
    pyproject = temp_git_repo / "pyproject.toml"
    pyproject.write_text('[project]\nname = "sync-tool"\ndependencies = ["fastapi", "click"]\n')

    info = ProjectWalker.inspect(temp_git_repo)
    assert info["name"] == temp_git_repo.name
    assert "Python" in info["tech_stack"]
    assert "FastAPI" in info["tech_stack"]
    assert "Click" in info["tech_stack"]
    assert info["readme_title"] == "Sync Engine"
    assert info["readme_description"] == "High performance sync"
