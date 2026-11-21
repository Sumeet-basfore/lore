"""Validation and rendering tests for generated SVG draft illustrations."""

import xml.etree.ElementTree as ET

import pytest
from pydantic import ValidationError

from lore.core.models import AtomType, ContentAtom, Draft, EvidenceRecord, Platform
from lore.visual.illustration import (
    IllustrationScene,
    build_illustration_prompt,
    fallback_illustration_scene,
    parse_illustration_scene,
    render_draft_illustration,
)


def make_draft(title="LinkedIn: Better auth checks", body="We replaced a timing-sensitive token check with a constant-time comparison."):
    return Draft(
        id="draft_test01",
        atom_id="atom_auth",
        project_id="project_lore",
        platform=Platform.LINKEDIN,
        title=title,
        raw_content=body,
        humanized_content=body,
    )


def make_atom() -> ContentAtom:
    return ContentAtom(
        id="atom_auth",
        project_id="project_lore",
        atom_type=AtomType.BUGFIX,
        title="Harden token verification",
        summary="Use a constant-time comparison for token identity.",
        evidence=EvidenceRecord(
            commits=["a1", "b2"],
            files_changed=4,
            insertions=120,
            deletions=31,
        ),
    )


def test_scene_schema_restricts_primitives_and_bounds():
    valid = {
        "shapes": [
            {"kind": "circle", "x": 10, "y": 10, "width": 20, "height": 20},
            {"kind": "rectangle", "x": 40, "y": 40, "width": 30, "height": 20, "tone": "rule"},
            {"kind": "line", "x": 0, "y": 0, "width": 60, "height": 80, "filled": False},
        ]
    }
    scene = IllustrationScene.model_validate(valid)
    assert len(scene.shapes) == 3

    valid["shapes"][0]["x"] = 90
    with pytest.raises(ValidationError, match="stay within"):
        IllustrationScene.model_validate(valid)

    valid["shapes"][0] = {"kind": "script", "x": 0, "y": 0, "width": 5, "height": 5}
    with pytest.raises(ValidationError):
        IllustrationScene.model_validate(valid)


def test_scene_parser_accepts_fenced_json_but_not_svg_markup():
    scene_json = fallback_illustration_scene().model_dump_json()
    parsed = parse_illustration_scene(f"```json\n{scene_json}\n```")
    assert parsed == fallback_illustration_scene()

    with pytest.raises(ValidationError):
        parse_illustration_scene('<svg onload="alert(1)"></svg>')


def test_renderer_emits_valid_self_contained_svg_and_exact_evidence():
    draft = make_draft()
    atom = make_atom()
    svg = render_draft_illustration(
        draft,
        "Lore",
        atom,
        fallback_illustration_scene(),
    )

    root = ET.fromstring(svg)
    rendered_text = " ".join(root.itertext())
    assert root.tag == "{http://www.w3.org/2000/svg}svg"
    assert root.attrib["viewBox"] == "0 0 1200 675"
    assert "LinkedIn: Better auth checks" in rendered_text
    assert "2 commits  ·  4 files  ·  +120 / −31 lines" in svg
    assert '<script' not in svg
    assert "href=" not in svg
    assert "onload=" not in svg


def test_renderer_escapes_user_text_and_provides_accessibility_metadata():
    draft = make_draft(title='Feature <script onload="bad()"> & tests')
    svg = render_draft_illustration(
        draft,
        'Repo <& "one"',
        make_atom(),
        fallback_illustration_scene(),
        aspect_ratio="1:1",
    )
    root = ET.fromstring(svg)

    assert root.attrib["viewBox"] == "0 0 1080 1080"
    assert root.attrib["aria-labelledby"] == "image-title image-description"
    assert "Feature &lt;script" in svg
    assert "&amp;" in svg
    assert "onload=\"bad()\"" not in svg


def test_scene_prompt_contains_draft_context_but_no_raw_diff():
    prompt = build_illustration_prompt(make_draft(), "Lore", make_atom(), "16:9")
    assert "Better auth checks" in prompt
    assert "constant-time comparison" in prompt
    assert '"commit_count": 2' in prompt
    assert "diff --git" not in prompt
    assert "file path" not in prompt.lower()


def test_fallback_scene_is_valid_and_renderer_rejects_unknown_aspect_ratio():
    scene = fallback_illustration_scene()
    assert len(scene.shapes) >= 3
    with pytest.raises(ValueError, match="aspect ratio"):
        render_draft_illustration(make_draft(), "Lore", make_atom(), scene, "4:3")
