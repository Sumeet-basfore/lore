"""CLI behavior for current-repository defaults and first-use setup."""

import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest
from click.testing import CliRunner

import lore.cli as cli_module
from lore.cli import main
from lore.core.database import Database
from lore.core.models import AtomType, ContentAtom, Draft, DraftStatus, EvidenceRecord, Platform, Project


@pytest.fixture
def runner(tmp_path, monkeypatch):
    monkeypatch.setenv("LORE_HOME", str(tmp_path / "lore-home"))
    monkeypatch.setenv("LORE_MOCK_LLM", "1")
    return CliRunner()


def make_repo(path: Path) -> None:
    path.mkdir(parents=True)
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    (path / "README.md").write_text("# Test repo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-m", "Add README"], cwd=path, check=True, capture_output=True)


def add_project(db: Database, path: Path, name: str) -> Project:
    project = Project(id=f"project-{name}", name=name, path=str(path.resolve()))
    db.add_project(project)
    return project


def add_atom(db: Database, project: Project, atom_id: str, title: str, status: str = "unprocessed") -> None:
    db.save_atom(
        ContentAtom(
            id=atom_id,
            project_id=project.id,
            atom_type=AtomType.FEATURE,
            title=title,
            summary=f"Implemented {title}",
            evidence=EvidenceRecord(commits=["abc123"], sample_messages=[f"feat: {title}"]),
            status=status,
            created_at=datetime.now(timezone.utc),
        )
    )


def add_draft(db: Database, project: Project, draft_id: str, title: str) -> None:
    atom_id = f"atom-{draft_id}"
    add_atom(db, project, atom_id, title)
    db.save_draft(
        Draft(
            id=draft_id,
            atom_id=atom_id,
            project_id=project.id,
            platform=Platform.LINKEDIN,
            title=title,
            raw_content=title,
            humanized_content=title,
            status=DraftStatus.DRAFTED,
        )
    )


def test_bare_lore_shows_current_repository_without_registering(runner, tmp_path, monkeypatch):
    repo = tmp_path / "unregistered-repo"
    make_repo(repo)
    monkeypatch.chdir(repo)

    result = runner.invoke(main, [])

    assert result.exit_code == 0
    assert "Current repository" in result.output
    assert "not registered" in result.output.lower()
    assert Database().list_projects() == []


def test_project_command_from_unregistered_repo_requires_setup_noninteractively(
    runner, tmp_path, monkeypatch
):
    repo = tmp_path / "new-repo"
    make_repo(repo)
    monkeypatch.chdir(repo)

    result = runner.invoke(main, ["atoms"])

    assert result.exit_code != 0
    assert "lore project add ." in result.output
    assert Database().list_projects() == []


def test_project_command_prompts_before_registering_repo(runner, tmp_path, monkeypatch):
    repo = tmp_path / "new-repo"
    make_repo(repo)
    monkeypatch.chdir(repo)
    monkeypatch.setattr(cli_module, "_is_interactive", lambda: True)

    result = runner.invoke(main, ["atoms"], input="y\n")

    assert result.exit_code == 0
    assert "Project registered" in result.output
    registered = Database().get_project_by_path(repo)
    assert registered is not None
    assert registered.name == repo.name


def test_project_command_respects_registration_decline(runner, tmp_path, monkeypatch):
    repo = tmp_path / "new-repo"
    make_repo(repo)
    monkeypatch.chdir(repo)
    monkeypatch.setattr(cli_module, "_is_interactive", lambda: True)

    result = runner.invoke(main, ["atoms"], input="n\n")

    assert result.exit_code != 0
    assert "No project was added" in result.output
    assert Database().list_projects() == []


def test_project_add_from_nested_directory_registers_git_root(runner, tmp_path, monkeypatch):
    repo = tmp_path / "repo-root"
    nested = repo / "src" / "module"
    make_repo(repo)
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)

    result = runner.invoke(main, ["project", "add", ".", "--name", "Root Project"])

    assert result.exit_code == 0
    registered = Database().get_project_by_path(repo)
    assert registered is not None
    assert registered.path == str(repo.resolve())


def test_project_scoped_atoms_default_to_current_repo(runner, tmp_path, monkeypatch):
    current_repo = tmp_path / "current-repo"
    other_repo = tmp_path / "other-repo"
    make_repo(current_repo)
    make_repo(other_repo)
    db = Database()
    current_project = add_project(db, current_repo, "Current")
    other_project = add_project(db, other_repo, "Other")
    add_atom(db, current_project, "atom-current", "Current change")
    add_atom(db, other_project, "atom-other", "Other change")
    monkeypatch.chdir(current_repo)

    result = runner.invoke(main, ["atoms"])

    assert result.exit_code == 0
    assert "Current change" in result.output
    assert "Other change" not in result.output


def test_explicit_project_overrides_current_repo(runner, tmp_path, monkeypatch):
    current_repo = tmp_path / "current-repo"
    other_repo = tmp_path / "other-repo"
    make_repo(current_repo)
    make_repo(other_repo)
    db = Database()
    current_project = add_project(db, current_repo, "Current")
    other_project = add_project(db, other_repo, "Other")
    add_atom(db, current_project, "atom-current", "Current change")
    add_atom(db, other_project, "atom-other", "Other change")
    monkeypatch.chdir(current_repo)

    result = runner.invoke(main, ["atoms", "--project", "Other"])

    assert result.exit_code == 0
    assert "Other change" in result.output
    assert "Current change" not in result.output


def test_scan_defaults_to_current_repository(runner, tmp_path, monkeypatch):
    current_repo = tmp_path / "current-repo"
    other_repo = tmp_path / "other-repo"
    make_repo(current_repo)
    make_repo(other_repo)
    db = Database()
    add_project(db, current_repo, "Current")
    add_project(db, other_repo, "Other")
    monkeypatch.chdir(current_repo)

    result = runner.invoke(main, ["scan", "--since", "365 days ago"])

    assert result.exit_code == 0
    assert "Current:" in result.output
    assert "Other:" not in result.output


def test_scan_all_remains_explicit_batch_operation(runner, tmp_path, monkeypatch):
    repo_a = tmp_path / "repo-a"
    repo_b = tmp_path / "repo-b"
    make_repo(repo_a)
    make_repo(repo_b)
    db = Database()
    add_project(db, repo_a, "Project A")
    add_project(db, repo_b, "Project B")
    monkeypatch.chdir(repo_a)

    result = runner.invoke(main, ["scan", "--all", "--since", "365 days ago"])

    assert result.exit_code == 0
    assert "Project A:" in result.output
    assert "Project B:" in result.output


def test_scan_rejects_conflicting_project_and_all_flags(runner):
    result = runner.invoke(main, ["scan", "--project", "Alpha", "--all"])

    assert result.exit_code != 0
    assert "either --all or --project" in result.output


def test_generate_rejects_atom_from_different_project(runner, tmp_path, monkeypatch):
    repo_a = tmp_path / "repo-a"
    repo_b = tmp_path / "repo-b"
    make_repo(repo_a)
    make_repo(repo_b)
    db = Database()
    project_a = add_project(db, repo_a, "Project A")
    add_project(db, repo_b, "Project B")
    add_atom(db, project_a, "atom-a", "Change A")

    result = runner.invoke(main, ["generate", "--atom", "atom-a", "--project", "Project B"])

    assert result.exit_code != 0
    assert "does not belong" in result.output


def test_export_filters_to_current_project(runner, tmp_path, monkeypatch):
    repo_a = tmp_path / "repo-a"
    repo_b = tmp_path / "repo-b"
    make_repo(repo_a)
    make_repo(repo_b)
    db = Database()
    project_a = add_project(db, repo_a, "Project A")
    project_b = add_project(db, repo_b, "Project B")
    add_draft(db, project_a, "draft-a", "Current project draft")
    add_draft(db, project_b, "draft-b", "Other project draft")
    monkeypatch.chdir(repo_a)
    output_dir = tmp_path / "exported"

    result = runner.invoke(main, ["export", "--status", "all", "--output-dir", str(output_dir)])

    assert result.exit_code == 0
    assert "Exported 1 draft(s)" in result.output
    exported = list(output_dir.iterdir())
    assert len(exported) == 1
    assert "current_project_draft" in exported[0].name


def test_terminal_review_defaults_to_current_project(runner, tmp_path, monkeypatch):
    repo_a = tmp_path / "repo-a"
    repo_b = tmp_path / "repo-b"
    make_repo(repo_a)
    make_repo(repo_b)
    db = Database()
    project_a = add_project(db, repo_a, "Project A")
    project_b = add_project(db, repo_b, "Project B")
    add_draft(db, project_a, "draft-a", "Current project draft")
    add_draft(db, project_b, "draft-b", "Other project draft")
    monkeypatch.chdir(repo_b)
    monkeypatch.setattr("lore.cli.click.getchar", lambda: "q")

    result = runner.invoke(main, ["review"])

    assert result.exit_code == 0
    assert "Other project draft" in result.output
    assert "Current project draft" not in result.output


def test_generation_requires_project_when_unscoped_atoms_span_projects(runner, tmp_path, monkeypatch):
    repo_a = tmp_path / "repo-a"
    repo_b = tmp_path / "repo-b"
    make_repo(repo_a)
    make_repo(repo_b)
    db = Database()
    project_a = add_project(db, repo_a, "Project A")
    project_b = add_project(db, repo_b, "Project B")
    add_atom(db, project_a, "atom-a", "Change A")
    add_atom(db, project_b, "atom-b", "Change B")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(main, ["generate"])

    assert result.exit_code != 0
    assert "multiple projects" in result.output.lower()
    assert "--project" in result.output


def test_generation_checks_all_projects_even_when_only_one_has_unprocessed_atoms(
    runner, tmp_path, monkeypatch
):
    repo_a = tmp_path / "repo-a"
    repo_b = tmp_path / "repo-b"
    make_repo(repo_a)
    make_repo(repo_b)
    db = Database()
    project_a = add_project(db, repo_a, "Project A")
    project_b = add_project(db, repo_b, "Project B")
    add_atom(db, project_a, "atom-a", "Available change")
    add_atom(db, project_b, "atom-b", "Previously drafted change", status="drafted")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(main, ["generate"])

    assert result.exit_code != 0
    assert "multiple projects" in result.output.lower()


def test_generation_defaults_to_current_project(runner, tmp_path, monkeypatch):
    repo_a = tmp_path / "repo-a"
    repo_b = tmp_path / "repo-b"
    make_repo(repo_a)
    make_repo(repo_b)
    db = Database()
    project_a = add_project(db, repo_a, "Project A")
    project_b = add_project(db, repo_b, "Project B")
    add_atom(db, project_a, "atom-a", "Change A")
    add_atom(db, project_b, "atom-b", "Change B")
    monkeypatch.chdir(repo_a)

    result = runner.invoke(main, ["generate", "--platform", "linkedin"])

    assert result.exit_code == 0
    drafts = db.list_drafts(project_id=project_a.id)
    assert len(drafts) == 1
    assert db.list_drafts(project_id=project_b.id) == []


def test_review_project_flag_is_rejected_for_web_dashboard(runner):
    result = runner.invoke(main, ["review", "--project", "Project A", "--web"])

    assert result.exit_code != 0
    assert "currently shows all projects" in result.output
