"""Integration tests for Lore CLI commands using Click CliRunner."""

import tempfile
from pathlib import Path
import pytest
from click.testing import CliRunner

from lore.cli import main
from lore.config import load_config
from lore.core.database import Database
from lore.generation.router import LLMRouter


@pytest.fixture
def cli_runner(tmp_path, monkeypatch):
    monkeypatch.setenv("LORE_HOME", str(tmp_path))
    monkeypatch.setenv("LORE_MOCK_LLM", "1")
    runner = CliRunner()
    return runner


def test_cli_help(cli_runner):
    result = cli_runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Lore: CLI-first developer content engine" in result.output


def test_cli_config(cli_runner):
    result = cli_runner.invoke(main, ["config", "list"])
    assert result.exit_code == 0
    assert "llm_provider" in result.output

    set_res = cli_runner.invoke(main, ["config", "set", "author_name", "DevSumeet"])
    assert set_res.exit_code == 0
    assert "DevSumeet" in set_res.output


def test_cli_config_never_prints_api_key(cli_runner):
    api_key = "test-key-do-not-display"

    set_res = cli_runner.invoke(main, ["config", "set", "api_key", api_key])
    assert set_res.exit_code == 0
    assert api_key not in set_res.output
    assert "value hidden" in set_res.output

    list_res = cli_runner.invoke(main, ["config", "list"])
    assert list_res.exit_code == 0
    assert api_key not in list_res.output
    assert "REDACTED" in list_res.output


def test_init_prompts_for_model_when_provider_changes(cli_runner):
    result = cli_runner.invoke(main, ["init"], input="Test Dev\n@testdev\nopenai\nexample-model\n")

    assert result.exit_code == 0
    assert "OpenAI Model" in result.output
    config = load_config()
    assert config.llm_provider == "openai"
    assert config.llm_model == "example-model"


def test_cli_project_flow(cli_runner, tmp_path):
    # Create fake repo dir
    fake_repo = tmp_path / "test_repo"
    fake_repo.mkdir()
    (fake_repo / "README.md").write_text("# My Test App\n> A great app\n")

    # Add project
    res = cli_runner.invoke(main, ["project", "add", str(fake_repo), "--name", "TestApp"])
    assert res.exit_code == 0
    assert "Registered project 'TestApp'" in res.output

    # List projects
    list_res = cli_runner.invoke(main, ["project", "list"])
    assert list_res.exit_code == 0
    assert "TestApp" in list_res.output


def test_cli_full_scan_generate_export_flow(cli_runner, tmp_path):
    import subprocess
    # Create a real temporary git repo
    repo = tmp_path / "app_repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=str(repo), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test Dev"], cwd=str(repo), check=True)
    subprocess.run(["git", "config", "user.email", "dev@example.com"], cwd=str(repo), check=True)

    code_file = repo / "main.py"
    code_file.write_text("print('hello world')\n")
    subprocess.run(["git", "add", "main.py"], cwd=str(repo), check=True)
    subprocess.run(["git", "commit", "-m", "feat(core): add core entrypoint"], cwd=str(repo), check=True)

    # 1. Project add
    res_add = cli_runner.invoke(main, ["project", "add", str(repo), "--name", "CoreApp"])
    assert res_add.exit_code == 0

    # 2. Scan
    res_scan = cli_runner.invoke(main, ["scan", "--project", "CoreApp"])
    assert res_scan.exit_code == 0
    assert "Extracted" in res_scan.output

    # 3. Atoms
    res_atoms = cli_runner.invoke(main, ["atoms", "--project", "CoreApp"])
    assert res_atoms.exit_code == 0
    assert "core entrypoint" in res_atoms.output.lower()

    # 4. Generate
    res_gen = cli_runner.invoke(main, ["generate", "--project", "CoreApp", "--platform", "twitter"])
    assert res_gen.exit_code == 0
    assert "Draft ID:" in res_gen.output
    # Extract draft ID
    lines = [line for line in res_gen.output.splitlines() if "Draft ID:" in line]
    assert len(lines) > 0
    draft_id = lines[0].split("Draft ID:")[1].strip()

    # 5. List Drafts
    res_drafts = cli_runner.invoke(main, ["drafts"])
    assert res_drafts.exit_code == 0
    assert draft_id[:8] in res_drafts.output

    # 6. Show Draft
    res_show = cli_runner.invoke(main, ["draft", "show", draft_id])
    assert res_show.exit_code == 0
    assert "Draft draft_" in res_show.output

    # 7. Approve Draft
    res_app = cli_runner.invoke(main, ["draft", "approve", draft_id])
    assert res_app.exit_code == 0
    assert "APPROVED" in res_app.output

    # 8. Calendar
    res_cal = cli_runner.invoke(main, ["calendar"])
    assert res_cal.exit_code == 0
    assert "Suggested Content Calendar" in res_cal.output

    # 9. Export
    export_dir = tmp_path / "exports"
    res_exp = cli_runner.invoke(main, ["export", "--status", "approved", "--output-dir", str(export_dir)])
    assert res_exp.exit_code == 0
    assert "Exported 1 draft(s)" in res_exp.output
    exported_files = list(export_dir.glob("*.md"))
    assert len(exported_files) == 1
    assert "twitter" in exported_files[0].name


def test_generation_failure_does_not_create_mock_draft(cli_runner, tmp_path, monkeypatch):
    import subprocess

    repo = tmp_path / "failing_repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=str(repo), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test Dev"], cwd=str(repo), check=True)
    subprocess.run(["git", "config", "user.email", "dev@example.com"], cwd=str(repo), check=True)
    (repo / "main.py").write_text("print('hello')\n")
    subprocess.run(["git", "add", "main.py"], cwd=str(repo), check=True)
    subprocess.run(["git", "commit", "-m", "feat: add entrypoint"], cwd=str(repo), check=True, capture_output=True)

    assert cli_runner.invoke(main, ["project", "add", str(repo), "--name", "FailingApp"]).exit_code == 0
    assert cli_runner.invoke(main, ["scan", "--project", "FailingApp"]).exit_code == 0

    def fail_generation(*args, **kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(LLMRouter, "generate", fail_generation)
    result = cli_runner.invoke(main, ["generate", "--project", "FailingApp"])

    assert result.exit_code != 0
    assert "LLM generation failed" in result.output
    assert "Falling back to mock" not in result.output
    assert Database().list_drafts() == []

