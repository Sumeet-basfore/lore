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
from typing import Optional

from lore.config import get_lore_home
from lore.visual.ast_diff_truncator import truncate_diff_for_card
from lore.visual.layout_engine import render_diff_svg
from lore.visual.themes import get_theme


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

    svg_path = dest_path.with_suffix(".svg")
    svg_path.write_text(svg_content, encoding="utf-8")

    if dest_path.suffix.lower() == ".svg":
        return svg_path

    freeze_bin = shutil.which("freeze")
    if freeze_bin:
        try:
            res = subprocess.run(
                [freeze_bin, str(svg_path), "-o", str(dest_path)],
                capture_output=True,
                timeout=10,
            )
            if res.returncode == 0 and dest_path.exists() and dest_path.stat().st_size > 0:
                return dest_path
        except Exception:
            pass

    try:
        import resvg_py
        png_bytes = resvg_py.svg_to_bytes(svg_content)
        dest_path.write_bytes(png_bytes)
        return dest_path
    except ImportError:
        pass
    except Exception:
        pass

    try:
        import cairosvg
        cairosvg.svg2png(bytestring=svg_content.encode("utf-8"), write_to=str(dest_path))
        return dest_path
    except ImportError:
        pass
    except Exception:
        pass

    return svg_path