"""Tests for Lore Visual Engine (Diff Truncator, Themes, Layout Engine, Card Generator)."""

from pathlib import Path
from types import SimpleNamespace
import sys
import pytest

from lore.visual.ast_diff_truncator import truncate_diff_for_card
from lore.visual.card_generator import PNG_SIGNATURE, generate_diff_card
from lore.visual.layout_engine import CardLayout, render_diff_svg
from lore.visual.themes import THEMES, get_theme, verify_theme_contrast


SAMPLE_DIFF = """
diff --git a/src/auth.py b/src/auth.py
index 1111111..2222222 100644
--- a/src/auth.py
+++ b/src/auth.py
@@ -10,6 +10,12 @@ def authenticate_user(username: str, token: str) -> bool:
     if not username:
         return False
-    # Old insecure check
-    return verify_token_v1(token)
+    # New hardened constant-time comparison
+    claims = decode_jwt_token(token)
+    if not claims or claims.is_expired():
+        return False
+    return hmac.compare_digest(claims.user, username)
"""

LONG_LINE_DIFF = """
@@ -1,3 +1,3 @@
-def query(): pass
+def query(): return execute_heavy_distributed_transaction_with_multiple_parameters(param_one, param_two, param_three, param_four, param_five, param_six, param_seven)
"""


def test_theme_wcag_contrast_ratios():
    """Verify all 3 themes mathematically pass WCAG AA (>4.5:1)."""
    for name, theme in THEMES.items():
        results = verify_theme_contrast(theme)
        for token, ratio in results.items():
            assert ratio >= 4.5, f"Theme {name} token {token} failed WCAG AA: {ratio:.2f}:1"


def test_diff_truncator_hard_wrap_ban():
    """Verify lines longer than 84 columns are strictly truncated with '…' and never wrapped."""
    formatted = truncate_diff_for_card(LONG_LINE_DIFF, max_lines=14, max_cols=84)
    assert len(formatted.lines) > 0
    for line in formatted.lines:
        assert len(line.content) <= 84
    add_line = next(l for l in formatted.lines if l.line_type == "add")
    assert add_line.content.endswith("…")


def test_diff_truncator_empty_and_binary():
    """Verify empty and binary diffs produce clean structured metadata cards."""
    empty_diff = truncate_diff_for_card("")
    assert empty_diff.is_empty_or_binary is True
    assert len(empty_diff.lines) > 0

    binary_diff = truncate_diff_for_card("Binary files a/logo.png and b/logo.png differ")
    assert binary_diff.is_empty_or_binary is True
    assert "Binary file" in binary_diff.lines[0].content


def test_layout_engine_renders_valid_svg():
    """Verify SVG layout includes macOS window controls and tag pill."""
    formatted = truncate_diff_for_card(SAMPLE_DIFF, max_lines=14)
    theme = get_theme("tokyo_night")
    svg = render_diff_svg(formatted, theme=theme, aspect_ratio="16:9")

    assert svg.startswith("<svg")
    assert svg.endswith("</svg>")
    assert "#FF5F56" in svg  # Close traffic light
    assert "#FFBD2E" in svg  # Minimize traffic light
    assert "#27C93F" in svg  # Maximize traffic light
    assert "lore.dev/diff" in svg
    assert "auth.py" in svg


def test_layout_engine_aspect_ratio_1_1():
    """Verify 1:1 aspect ratio renders square 1080x1080 with bottom stat bar."""
    formatted = truncate_diff_for_card(SAMPLE_DIFF, max_lines=20)
    svg = render_diff_svg(formatted, aspect_ratio="1:1")

    assert 'viewBox="0 0 1080 1080"' in svg
    assert "LOC" in svg


def test_card_generator_svg_output_does_not_require_a_rasterizer(tmp_path):
    """SVG output remains available without optional raster tools."""
    out_target = tmp_path / "card.svg"
    result_path = generate_diff_card(
        diff_text=SAMPLE_DIFF,
        output_path=out_target,
        theme_name="catppuccin_mocha",
        aspect_ratio="16:9",
    )
    assert result_path == out_target
    assert result_path.read_text(encoding="utf-8").startswith("<svg")


def test_card_generator_png_output_is_actually_png(tmp_path, monkeypatch):
    """Raster output is validated rather than accepted by file existence alone."""
    monkeypatch.setattr("lore.visual.card_generator.shutil.which", lambda _: None)
    monkeypatch.setitem(
        sys.modules,
        "resvg_py",
        SimpleNamespace(svg_to_bytes=lambda _: PNG_SIGNATURE + b"rendered"),
    )

    out_target = tmp_path / "card.png"
    result_path = generate_diff_card(
        diff_text=SAMPLE_DIFF,
        output_path=out_target,
        theme_name="catppuccin_mocha",
        aspect_ratio="16:9",
    )

    assert result_path == out_target
    assert out_target.read_bytes().startswith(PNG_SIGNATURE)
    assert out_target.with_suffix(".svg").is_file()


def test_png_request_explains_missing_rasterizer_and_keeps_svg(tmp_path, monkeypatch):
    """A missing rasterizer reports an actionable error and never returns an SVG as PNG."""
    monkeypatch.setattr("lore.visual.card_generator.shutil.which", lambda _: None)
    monkeypatch.setitem(sys.modules, "resvg_py", None)
    monkeypatch.setitem(sys.modules, "cairosvg", None)

    out_target = tmp_path / "card.png"
    with pytest.raises(RuntimeError, match="Could not render PNG") as error:
        generate_diff_card(
            diff_text=SAMPLE_DIFF,
            output_path=out_target,
            theme_name="catppuccin_mocha",
            aspect_ratio="16:9",
        )

    assert "card.svg" in str(error.value)
    assert out_target.with_suffix(".svg").is_file()
    assert not out_target.exists()
