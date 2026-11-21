"""CLI integration tests for draft-linked SVG and PNG image generation."""

import sys
import struct
from types import SimpleNamespace
from pathlib import Path
import zlib

from click.testing import CliRunner

from lore.cli import main
from lore.core.database import Database
from lore.core.models import AtomType, ContentAtom, Draft, EvidenceRecord, Platform, Project
from lore.visual.card_generator import PNG_SIGNATURE


def png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    checksum = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", checksum)


PNG_SAMPLE = (
    PNG_SIGNATURE
    + png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    + png_chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00"))
    + png_chunk(b"IEND", b"")
)


def add_draft(db: Database, repo: Path, draft_id: str = "draft-image-1") -> Draft:
    project = Project(id="project-images", name="Image Demo", path=str(repo.resolve()))
    db.add_project(project)
    atom = ContentAtom(
        id="atom-images",
        project_id=project.id,
        atom_type=AtomType.FEATURE,
        title="Add image generation",
        summary="Generate vector art from a content draft.",
        evidence=EvidenceRecord(
            commits=["abc123"],
            files_changed=3,
            insertions=75,
            deletions=12,
        ),
    )
    db.save_atom(atom)
    draft = Draft(
        id=draft_id,
        atom_id=atom.id,
        project_id=project.id,
        platform=Platform.LINKEDIN,
        title="LinkedIn: Add vector images",
        raw_content="Draft copy",
        humanized_content="Lore can now make an editable illustration from a reviewed draft.",
    )
    db.save_draft(draft)
    return draft


def setup(runner: CliRunner, tmp_path: Path, monkeypatch) -> tuple[Database, Draft, Path]:
    home = tmp_path / "lore-home"
    repo = tmp_path / "project with spaces"
    home.mkdir()
    repo.mkdir()
    monkeypatch.setenv("LORE_HOME", str(home))
    monkeypatch.setenv("LORE_MOCK_LLM", "1")
    db = Database()
    return db, add_draft(db, repo), repo


def test_image_command_writes_svg_and_attaches_dashboard_preview(tmp_path, monkeypatch):
    runner = CliRunner()
    db, draft, repo = setup(runner, tmp_path, monkeypatch)

    result = runner.invoke(main, ["image", "generate", draft.id])

    svg_path = repo / "lore-media" / f"{draft.id}.svg"
    assert result.exit_code == 0, result.output
    assert svg_path.is_file()
    svg = svg_path.read_text(encoding="utf-8")
    assert "LinkedIn: Add vector images" in svg
    assert "1 commits  ·  3 files  ·  +75 / −12 lines" in svg
    assert db.get_draft(draft.id).card_image_path == str(svg_path)
    assert "lore review --web" in result.output


def test_png_mode_saves_svg_source_and_upload_ready_png(tmp_path, monkeypatch):
    runner = CliRunner()
    db, draft, repo = setup(runner, tmp_path, monkeypatch)
    monkeypatch.setattr("lore.visual.card_generator.shutil.which", lambda _: None)
    monkeypatch.setitem(
        sys.modules,
        "resvg_py",
        SimpleNamespace(
            svg_to_bytes=lambda _: PNG_SAMPLE
        ),
    )

    result = runner.invoke(main, ["image", "generate", draft.id, "--format", "png"])

    svg_path = repo / "lore-media" / f"{draft.id}.svg"
    png_path = repo / "lore-media" / f"{draft.id}.png"
    assert result.exit_code == 0, result.output
    assert svg_path.is_file()
    assert png_path.read_bytes().startswith(PNG_SIGNATURE)
    assert db.get_draft(draft.id).card_image_path == str(png_path)


def test_missing_png_renderer_keeps_svg_and_links_it(tmp_path, monkeypatch):
    runner = CliRunner()
    db, draft, repo = setup(runner, tmp_path, monkeypatch)
    monkeypatch.setattr("lore.visual.card_generator.shutil.which", lambda _: None)
    monkeypatch.setitem(sys.modules, "resvg_py", None)
    monkeypatch.setitem(sys.modules, "cairosvg", None)

    result = runner.invoke(main, ["image", "generate", draft.id, "--format", "png"])

    svg_path = repo / "lore-media" / f"{draft.id}.svg"
    png_path = repo / "lore-media" / f"{draft.id}.png"
    assert result.exit_code != 0
    assert "Could not render PNG" in result.output
    assert svg_path.is_file()
    assert not png_path.exists()
    assert db.get_draft(draft.id).card_image_path == str(svg_path)


def test_image_command_refuses_output_outside_dashboard_sandbox(tmp_path, monkeypatch):
    runner = CliRunner()
    db, draft, _ = setup(runner, tmp_path, monkeypatch)
    outside = tmp_path / "outside"

    result = runner.invoke(main, ["image", "generate", draft.id, "--output-dir", str(outside)])

    assert result.exit_code != 0
    assert "inside the draft's project or Lore's data directory" in result.output
    assert not outside.exists()
    assert db.get_draft(draft.id).card_image_path is None


def test_image_command_refuses_to_follow_output_symlinks(tmp_path, monkeypatch):
    runner = CliRunner()
    db, draft, repo = setup(runner, tmp_path, monkeypatch)
    output_dir = repo / "lore-media"
    output_dir.mkdir()
    outside_file = tmp_path / "do-not-overwrite.svg"
    outside_file.write_text("keep me", encoding="utf-8")
    (output_dir / f"{draft.id}.svg").symlink_to(outside_file)

    result = runner.invoke(main, ["image", "generate", draft.id, "--force"])

    assert result.exit_code != 0
    assert "symbolic link" in result.output
    assert outside_file.read_text(encoding="utf-8") == "keep me"
    assert db.get_draft(draft.id).card_image_path is None


def test_image_command_requires_force_before_replacing_an_asset(tmp_path, monkeypatch):
    runner = CliRunner()
    db, draft, repo = setup(runner, tmp_path, monkeypatch)
    generated = runner.invoke(main, ["image", "generate", draft.id])
    assert generated.exit_code == 0, generated.output
    svg_path = repo / "lore-media" / f"{draft.id}.svg"
    assert svg_path.read_text(encoding="utf-8")

    refused = runner.invoke(main, ["image", "generate", draft.id])
    replaced = runner.invoke(main, ["image", "generate", draft.id, "--force"])

    assert refused.exit_code != 0
    assert "Use --force" in refused.output
    assert replaced.exit_code == 0, replaced.output
    assert svg_path.read_text(encoding="utf-8")
    assert db.get_draft(draft.id).card_image_path == str(svg_path)


def test_draft_show_displays_attached_image_path(tmp_path, monkeypatch):
    runner = CliRunner()
    db, draft, _ = setup(runner, tmp_path, monkeypatch)
    result = runner.invoke(main, ["image", "generate", draft.id])

    shown = runner.invoke(main, ["draft", "show", draft.id])

    assert result.exit_code == 0, result.output
    assert shown.exit_code == 0, shown.output
    assert "Image preview:" in shown.output
