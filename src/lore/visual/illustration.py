"""Validated vector scenes for draft-linked editorial illustrations."""

import html
import json
import re
import textwrap
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from lore.core.models import ContentAtom, Draft


class IllustrationShape(BaseModel):
    """One bounded geometric primitive in the illustration panel."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["circle", "rectangle", "line", "diamond"]
    x: int = Field(ge=0, le=100, description="Left position, as a percentage of the panel.")
    y: int = Field(ge=0, le=100, description="Top position, as a percentage of the panel.")
    width: int = Field(ge=0, le=100, description="Width, as a percentage of the panel.")
    height: int = Field(ge=0, le=100, description="Height, as a percentage of the panel.")
    tone: Literal["ink", "muted", "rule"] = "ink"
    filled: bool = True
    stroke_width: int = Field(default=2, ge=1, le=6)

    @model_validator(mode="after")
    def validate_geometry(self) -> "IllustrationShape":
        if self.x + self.width > 100 or self.y + self.height > 100:
            raise ValueError("Shape must stay within the illustration panel.")
        if self.kind == "line":
            if self.width == 0 and self.height == 0:
                raise ValueError("A line must have a non-zero length.")
        elif self.width == 0 or self.height == 0:
            raise ValueError("Filled shapes need non-zero width and height.")
        return self


class IllustrationScene(BaseModel):
    """Model-authored artwork data; SVG elements are produced only by Lore."""

    model_config = ConfigDict(extra="forbid")

    shapes: list[IllustrationShape] = Field(min_length=3, max_length=24)


class IllustrationTone(str, Enum):
    INK = "#0B0F14"
    MUTED = "#52606D"
    RULE = "#D3DCE2"


_SCENE_SYSTEM_PROMPT = """Create a restrained geometric illustration for a developer-content card.
Return only one JSON object matching the supplied schema. Draw shapes only. Do not
write text, letters, numbers, a logo, SVG markup, paths, CSS, gradients, shadows,
external URLs, or scripts. Use the draft and evidence only to choose a clear visual
metaphor. The permitted tones are ink, muted, and rule. Keep the composition calm,
deliberate, and legible; avoid sparkles, confetti, random blobs, and dense decoration."""


def build_illustration_prompt(
    draft: Draft,
    project_name: str,
    atom: Optional[ContentAtom],
    aspect_ratio: str,
) -> str:
    """Build a bounded visual brief without including source files or diffs."""
    evidence = atom.evidence if atom else None
    source = {
        "project": project_name,
        "platform": draft.platform.value,
        "draft_title": draft.title or "Untitled draft",
        "draft_excerpt": _plain_text(draft.humanized_content)[:1200],
        "atom_title": atom.title if atom else None,
        "atom_summary": atom.summary[:800] if atom else None,
        "evidence": (
            {
                "commit_count": len(evidence.commits),
                "files_changed": evidence.files_changed,
                "insertions": evidence.insertions,
                "deletions": evidence.deletions,
            }
            if evidence
            else None
        ),
        "aspect_ratio": aspect_ratio,
    }
    return (
        "Choose a visual metaphor for the attached draft. Return between 6 and 18 "
        "geometric shapes arranged inside one square panel. Coordinates use integers "
        "from 0 to 100; x + width and y + height must each be at most 100. Use the "
        "fewest shapes that make the idea recognizable. The card text will be rendered "
        "separately from verified draft fields, so do not provide text.\n\n"
        f"Scene schema:\n{json.dumps(IllustrationScene.model_json_schema(), ensure_ascii=False)}\n\n"
        f"Draft context:\n{json.dumps(source, ensure_ascii=False)}"
    )


def parse_illustration_scene(raw_output: str) -> IllustrationScene:
    """Parse JSON scene data, including a common fenced-JSON wrapper."""
    candidate = raw_output.strip()
    if candidate.startswith("```"):
        lines = candidate.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        candidate = "\n".join(lines).strip()
    return IllustrationScene.model_validate_json(candidate)


def fallback_illustration_scene() -> IllustrationScene:
    """Return a small, deterministic evidence-strata motif when model JSON is invalid."""
    return IllustrationScene(
        shapes=[
            IllustrationShape(kind="line", x=20, y=12, width=0, height=76, tone="ink", filled=False, stroke_width=3),
            IllustrationShape(kind="circle", x=12, y=18, width=16, height=16, tone="muted", filled=False, stroke_width=2),
            IllustrationShape(kind="rectangle", x=24, y=34, width=52, height=8, tone="rule"),
            IllustrationShape(kind="rectangle", x=24, y=48, width=38, height=12, tone="ink"),
            IllustrationShape(kind="diamond", x=66, y=64, width=18, height=18, tone="muted", filled=False, stroke_width=2),
        ]
    )


def generate_illustration_scene(
    router,
    draft: Draft,
    project_name: str,
    atom: Optional[ContentAtom],
    aspect_ratio: str,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> tuple[IllustrationScene, bool]:
    """Ask the configured text model for shapes and use a safe motif on invalid JSON."""
    raw_output = router.generate(
        prompt=build_illustration_prompt(draft, project_name, atom, aspect_ratio),
        system_prompt=_SCENE_SYSTEM_PROMPT,
        provider=provider,
        model=model,
        temperature=0.2,
    )
    try:
        return parse_illustration_scene(raw_output), False
    except ValidationError:
        return fallback_illustration_scene(), True


def render_draft_illustration(
    draft: Draft,
    project_name: str,
    atom: Optional[ContentAtom],
    scene: IllustrationScene,
    aspect_ratio: str = "16:9",
) -> str:
    """Render a self-contained, static SVG card with source-backed text."""
    if aspect_ratio not in {"16:9", "1:1"}:
        raise ValueError("Illustration aspect ratio must be '16:9' or '1:1'.")

    width, height = (1200, 675) if aspect_ratio == "16:9" else (1080, 1080)
    paper = "#F4F7F8"
    ink = "#0B0F14"
    muted = "#52606D"
    rule = "#D3DCE2"
    evidence_color = "#1F7A3B"
    colors = {
        "ink": IllustrationTone.INK.value,
        "muted": IllustrationTone.MUTED.value,
        "rule": IllustrationTone.RULE.value,
    }

    if aspect_ratio == "16:9":
        divider_x = 690
        art_x, art_y, art_size = 730, 120, 430
        title_y, title_size, title_chars, title_lines = 156, 38, 27, 3
        excerpt_y, excerpt_chars, excerpt_lines = 324, 60, 3
    else:
        divider_x = 540
        art_x, art_y, art_size = 595, 300, 420
        title_y, title_size, title_chars, title_lines = 158, 34, 24, 4
        excerpt_y, excerpt_chars, excerpt_lines = 364, 42, 4

    title = _clean_text(draft.title or "Engineering update")
    excerpt = _first_paragraph(draft.humanized_content)
    title_rows = _wrap(title, title_chars, title_lines)
    excerpt_rows = _wrap(excerpt, excerpt_chars, excerpt_lines)
    evidence = atom.evidence if atom else None

    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="image-title image-description">',
        f"  <title id=\"image-title\">{_xml_text(title)}</title>",
        f'  <desc id="image-description">Editorial draft card for {_xml_text(project_name)}. Text comes from the draft; evidence counts come from its linked content atom.</desc>',
        f'  <rect width="{width}" height="{height}" fill="{paper}"/>',
        f'  <text x="64" y="76" fill="{muted}" font-family="Source Sans 3, Arial, sans-serif" font-size="16" font-weight="600" letter-spacing="1.5">LORE  /  {html.escape(draft.platform.value.upper())}</text>',
        f'  <line x1="{divider_x}" y1="64" x2="{divider_x}" y2="{height - 64}" stroke="{rule}" stroke-width="2"/>',
        _render_text(title_rows, 64, title_y, title_size, 1.16, ink, "700"),
        _render_text(excerpt_rows, 64, excerpt_y, 19 if aspect_ratio == "16:9" else 18, 1.55, muted, "400"),
        f'  <text x="64" y="{height - 105}" fill="{muted}" font-family="JetBrains Mono, Consolas, monospace" font-size="13" font-weight="500" letter-spacing="1">COMMIT METADATA</text>',
    ]

    if evidence:
        evidence_line = (
            f"{len(evidence.commits)} commits  ·  {evidence.files_changed} files  ·  "
            f"+{evidence.insertions} / −{evidence.deletions} lines"
        )
        elements.append(
            f'  <text x="64" y="{height - 70}" fill="{evidence_color}" font-family="Source Sans 3, Arial, sans-serif" font-size="18" font-weight="600">{_xml_text(evidence_line)}</text>'
        )
    else:
        elements.append(
            f'  <text x="64" y="{height - 70}" fill="{muted}" font-family="Source Sans 3, Arial, sans-serif" font-size="18">No linked commit metadata</text>'
        )

    elements.append(
        f'  <text x="{width - 64}" y="{height - 40}" text-anchor="end" fill="{muted}" font-family="Source Sans 3, Arial, sans-serif" font-size="13">{_xml_text(project_name)}</text>'
    )
    elements.append(f'  <g transform="translate({art_x} {art_y}) scale({art_size / 100:.2f})">')
    for shape in scene.shapes:
        elements.append(_render_shape(shape, colors))
    elements.extend(["  </g>", "</svg>"])
    return "\n".join(elements)


def _render_shape(shape: IllustrationShape, colors: dict[str, str]) -> str:
    color = colors[shape.tone]
    fill = color if shape.filled and shape.kind != "line" else "none"
    stroke = color
    common = f'fill="{fill}" stroke="{stroke}" stroke-width="{shape.stroke_width}"'
    if shape.kind == "circle":
        return (
            f'    <ellipse cx="{shape.x + shape.width / 2:g}" cy="{shape.y + shape.height / 2:g}" '
            f'rx="{shape.width / 2:g}" ry="{shape.height / 2:g}" {common}/>'
        )
    if shape.kind == "rectangle":
        return (
            f'    <rect x="{shape.x}" y="{shape.y}" width="{shape.width}" height="{shape.height}" '
            f'rx="{min(shape.width, shape.height) * 0.08:g}" {common}/>'
        )
    if shape.kind == "line":
        return (
            f'    <line x1="{shape.x}" y1="{shape.y}" x2="{shape.x + shape.width}" '
            f'y2="{shape.y + shape.height}" stroke="{stroke}" stroke-width="{shape.stroke_width}"/>'
        )
    mid_x = shape.x + shape.width / 2
    mid_y = shape.y + shape.height / 2
    points = (
        f"{mid_x:g},{shape.y} {shape.x + shape.width},{mid_y:g} "
        f"{mid_x:g},{shape.y + shape.height} {shape.x},{mid_y:g}"
    )
    return f'    <polygon points="{points}" {common}/>'


def _render_text(
    lines: list[str],
    x: int,
    y: int,
    font_size: int,
    line_height: float,
    fill: str,
    font_weight: str,
) -> str:
    tspans = "".join(
        f'<tspan x="{x}" dy="{0 if index == 0 else font_size * line_height:g}">{_xml_text(line)}</tspan>'
        for index, line in enumerate(lines)
    )
    return (
        f'  <text x="{x}" y="{y}" fill="{fill}" font-family="Bricolage Grotesque, Arial, sans-serif" '
        f'font-size="{font_size}" font-weight="{font_weight}">{tspans}</text>'
    )


def _first_paragraph(content: str) -> str:
    for paragraph in re.split(r"\n\s*\n", content.strip()):
        if paragraph.lstrip().startswith("```"):
            continue
        plain = _plain_text(paragraph)
        if plain:
            return plain
    return "A draft built from recent project work."


def _plain_text(content: str) -> str:
    text = re.sub(r"```.*?```", " ", content, flags=re.DOTALL)
    text = re.sub(r"!??\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"^\s{0,3}(?:#{1,6}\s*|[-*+]\s+|\d+[.)]\s+)", "", text, flags=re.MULTILINE)
    text = re.sub(r"[`*_>#]", "", text)
    return " ".join(_clean_text(text).split())


def _clean_text(value: str) -> str:
    return "".join(
        char
        for char in value
        if char in "\t\n\r"
        or (
            ord(char) >= 0x20
            and not 0xD800 <= ord(char) <= 0xDFFF
            and ord(char) not in {0xFFFE, 0xFFFF}
        )
    ).strip()


def _xml_text(value: str) -> str:
    return html.escape(_clean_text(value), quote=True)


def _wrap(value: str, width: int, max_lines: int) -> list[str]:
    lines = textwrap.wrap(value, width=width, break_long_words=True, break_on_hyphens=False) or [""]
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        final = lines[-1].rstrip(" .,:;!?…")
        lines[-1] = (final[: max(1, width - 1)].rstrip() + "…") if final else "…"
    return lines
