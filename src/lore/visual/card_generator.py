"""Multi-tier rasterizer and visual card exporter.

Tiers:
1. freeze CLI binary (if present in PATH)
2. resvg-py Python bindings
3. Pure standalone SVG fallback
"""

import hashlib
from pathlib import Path
import shutil
import subprocess
import uuid
from typing import Optional

from lore.config import get_lore_home
from lore.visual.ast_diff_truncator import truncate_diff_for_card
from lore.visual.layout_engine import render_diff_svg
from lore.visual.themes import get_theme

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def rasterize_svg_file(svg_path: Path, output_path: Path) -> Path:
    """Render an SVG file to a real PNG, or explain how to enable rasterization."""
    svg_path = Path(svg_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_name(f".{output_path.stem}.{uuid.uuid4().hex}.tmp.png")
    errors = []

    def accept_png() -> bool:
        return temp_path.is_file() and temp_path.read_bytes().startswith(PNG_SIGNATURE)

    try:
        freeze_bin = shutil.which("freeze")
        if freeze_bin:
            try:
                result = subprocess.run(
                    [freeze_bin, str(svg_path), "-o", str(temp_path)],
                    capture_output=True,
                    timeout=10,
                    check=False,
                )
                if result.returncode == 0 and accept_png():
                    temp_path.replace(output_path)
                    return output_path
                errors.append("freeze did not produce a valid PNG")
            except (OSError, subprocess.SubprocessError) as exc:
                errors.append(f"freeze: {exc}")

        try:
            import resvg_py

            png_bytes = resvg_py.svg_to_bytes(svg_path.read_text(encoding="utf-8"))
            if not isinstance(png_bytes, bytes) or not png_bytes.startswith(PNG_SIGNATURE):
                raise ValueError("resvg-py did not return PNG data")
            temp_path.write_bytes(png_bytes)
            temp_path.replace(output_path)
            return output_path
        except ImportError:
            errors.append("resvg-py is not installed")
        except Exception as exc:
            errors.append(f"resvg-py: {exc}")

        try:
            import cairosvg

            cairosvg.svg2png(url=str(svg_path), write_to=str(temp_path))
            if not accept_png():
                raise ValueError("CairoSVG did not produce a valid PNG")
            temp_path.replace(output_path)
            return output_path
        except ImportError:
            errors.append("CairoSVG is not installed")
        except Exception as exc:
            errors.append(f"CairoSVG: {exc}")

        detail = "; ".join(errors)
        raise RuntimeError(
            f"Could not render PNG. The SVG source is available at {svg_path}. "
            "Install resvg-py or CairoSVG, or add the 'freeze' renderer to PATH. "
            f"Renderer details: {detail}"
        )
    finally:
        temp_path.unlink(missing_ok=True)


def generate_diff_card(
    diff_text: str,
    output_path: Optional[Path] = None,
    theme_name: str = "tokyo_night",
    aspect_ratio: str = "16:9",
    file_label: Optional[str] = None,
) -> Path:
    """Generates a visual diff card PNG or SVG from git diff text."""
    theme = get_theme(theme_name)
    max_lines = 20 if aspect_ratio == "1:1" else 14
    max_cols = 80 if aspect_ratio == "1:1" else 84

    formatted = truncate_diff_for_card(
        diff_text=diff_text,
        max_lines=max_lines,
        max_cols=max_cols,
        file_label=file_label,
    )
    svg_content = render_diff_svg(
        diff=formatted,
        theme=theme,
        aspect_ratio=aspect_ratio,
        file_label=file_label,
    )

    if output_path is None:
        cards_dir = get_lore_home() / "cards"
        cards_dir.mkdir(parents=True, exist_ok=True)
        content_hash = hashlib.sha256(svg_content.encode("utf-8")).hexdigest()[:12]
        dest_path = cards_dir / f"diff_{content_hash}_{aspect_ratio.replace(':', '_')}.png"
    else:
        dest_path = Path(output_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)

    requested_suffix = dest_path.suffix.lower()
    if requested_suffix not in {".svg", ".png"}:
        raise ValueError("Visual cards support only .svg and .png output paths.")

    svg_path = dest_path.with_suffix(".svg")
    svg_path.write_text(svg_content, encoding="utf-8")

    if requested_suffix == ".svg":
        return svg_path
    return rasterize_svg_file(svg_path, dest_path)
