"""Font assets and typography metrics for Lore Visual Engine."""

from pathlib import Path
from typing import Dict

# Font typography settings
FONT_FAMILY_PRIMARY = "JetBrains Mono"
FONT_STACK = (
    "'JetBrains Mono', 'Fira Code', 'Cascadia Code', 'SF Mono', "
    "Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace"
)

# Monospace character aspect ratio (advance width = font_size * 0.6)
MONOSPACE_ASPECT_RATIO = 0.60


def get_font_dir() -> Path:
    """Returns the directory containing font assets."""
    return Path(__file__).parent


def calculate_text_width(text: str, font_size: float = 18.0) -> float:
    """Calculates deterministic text width for monospace fonts."""
    return len(text) * font_size * MONOSPACE_ASPECT_RATIO


def get_typography_metrics(aspect_ratio: str = "16:9") -> Dict[str, float]:
    """Returns typography and geometry parameters for the specified aspect ratio."""
    if aspect_ratio == "1:1":
        return {
            "card_width": 1080.0,
            "card_height": 1080.0,
            "font_size": 20.0,
            "line_height": 30.0,
            "max_lines": 20,
            "max_cols": 80,
            "char_width": 20.0 * MONOSPACE_ASPECT_RATIO,
            "window_margin": 40.0,
            "header_height": 48.0,
            "bottom_bar_height": 56.0,
        }
    # Default 16:9
    return {
        "card_width": 1200.0,
        "card_height": 675.0,
        "font_size": 18.0,
        "line_height": 26.0,
        "max_lines": 14,
        "max_cols": 84,
        "char_width": 18.0 * MONOSPACE_ASPECT_RATIO,
        "window_margin": 36.0,
        "header_height": 44.0,
        "bottom_bar_height": 0.0,
    }