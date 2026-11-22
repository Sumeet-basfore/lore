"""Lore Visual Diff Card Generator.

Headless code-to-image generator producing syntax-highlighted visual diff cards
for social media sharing and release artifacts.
"""

from lore.visual.ast_diff_truncator import (
    DiffLine,
    FormattedDiff,
    truncate_diff_for_card,
)
from lore.visual.card_generator import generate_diff_card
from lore.visual.layout_engine import CardLayout, render_diff_svg
from lore.visual.themes import THEMES, Theme, get_theme, verify_theme_contrast
from lore.visual.illustration import (
    IllustrationScene,
    IllustrationShape,
    fallback_illustration_scene,
    generate_illustration_scene,
    render_draft_illustration,
)

__all__ = [
    "DiffLine",
    "FormattedDiff",
    "truncate_diff_for_card",
    "Theme",
    "THEMES",
    "get_theme",
    "verify_theme_contrast",
    "CardLayout",
    "render_diff_svg",
    "generate_diff_card",
    "IllustrationScene",
    "IllustrationShape",
    "fallback_illustration_scene",
    "generate_illustration_scene",
    "render_draft_illustration",
]
