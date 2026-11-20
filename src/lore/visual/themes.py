"""Color themes with rigorous WCAG AA contrast verification for visual cards."""

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class Theme:
    """Syntax and window color palette for visual diff cards."""
    name: str
    display_name: str
    # Window and canvas
    bg_color: str          # Outer card background
    window_bg: str         # Code editor canvas
    header_bg: str         # Title bar background
    border_color: str      # Frame stroke
    # Code syntax
    text_color: str        # Default text (foreground)
    add_text: str          # Added code text (green)
    add_bg: str            # Added line highlight background
    del_text: str          # Deleted code text (red/coral)
    del_bg: str            # Deleted line highlight background
    line_number_color: str # Line numbers (muted)
    comment_color: str     # Comments and ellipsis (// ...)
    # Badges and UI
    pill_bg: str           # lore.dev/diff tag background
    pill_text: str         # lore.dev/diff tag text


TOKYO_NIGHT = Theme(
    name="tokyo_night",
    display_name="Tokyo Night",
    bg_color="#13141c",
    window_bg="#1a1b26",
    header_bg="#16161e",
    border_color="#292e42",
    text_color="#c0caf5",        # Contrast ~ 10.2:1
    add_text="#9ece6a",          # Contrast ~ 9.4:1
    add_bg="rgba(158, 206, 106, 0.15)",
    del_text="#f7768e",          # Contrast ~ 6.1:1
    del_bg="rgba(247, 118, 142, 0.15)",
    line_number_color="#7982a9",  # Contrast ~ 4.7:1
    comment_color="#7aa2f7",      # Contrast ~ 6.9:1
    pill_bg="#24283b",
    pill_text="#7aa2f7",         # Contrast on pill_bg ~ 5.8:1
)

CATPPUCCIN_MOCHA = Theme(
    name="catppuccin_mocha",
    display_name="Catppuccin Mocha",
    bg_color="#181825",
    window_bg="#1e1e2e",
    header_bg="#11111b",
    border_color="#313244",
    text_color="#cdd6f4",        # Contrast ~ 11.2:1
    add_text="#a6e3a1",          # Contrast ~ 11.3:1
    add_bg="rgba(166, 227, 161, 0.15)",
    del_text="#f38ba8",          # Contrast ~ 7.6:1
    del_bg="rgba(243, 139, 168, 0.15)",
    line_number_color="#898d9f",  # Contrast ~ 5.1:1
    comment_color="#9399b2",      # Contrast ~ 5.9:1
    pill_bg="#313244",
    pill_text="#89b4fa",         # Contrast on pill_bg ~ 5.9:1
)

ONE_DARK = Theme(
    name="one_dark",
    display_name="One Dark Pro",
    bg_color="#1b1d23",
    window_bg="#21252b",
    header_bg="#1d2026",
    border_color="#3e4451",
    text_color="#abb2bf",        # Contrast ~ 7.1:1
    add_text="#98c379",          # Contrast ~ 7.8:1
    add_bg="rgba(152, 195, 121, 0.15)",
    del_text="#e06c75",          # Contrast ~ 5.1:1
    del_bg="rgba(224, 108, 117, 0.15)",
    line_number_color="#8c92a0",  # Contrast ~ 5.0:1
    comment_color="#8c92a0",      # Contrast ~ 5.0:1
    pill_bg="#2c313a",
    pill_text="#61afef",         # Contrast on pill_bg ~ 5.8:1
)

THEMES: Dict[str, Theme] = {
    "tokyo_night": TOKYO_NIGHT,
    "catppuccin_mocha": CATPPUCCIN_MOCHA,
    "one_dark": ONE_DARK,
}


def get_theme(name: str = "tokyo_night") -> Theme:
    """Retrieves a theme by name, falling back to Tokyo Night."""
    normalized = name.lower().replace("-", "_").replace(" ", "_")
    return THEMES.get(normalized, TOKYO_NIGHT)


def _hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    clean = hex_str.lstrip("#")
    if len(clean) == 3:
        clean = "".join(c * 2 for c in clean)
    return int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16)


def _relative_luminance(r: int, g: int, b: int) -> float:
    def channel(c: int) -> float:
        v = c / 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def calculate_contrast_ratio(foreground_hex: str, background_hex: str) -> float:
    """Calculates the WCAG 2.1 contrast ratio between two hex colors."""
    r1, g1, b1 = _hex_to_rgb(foreground_hex)
    r2, g2, b2 = _hex_to_rgb(background_hex)
    l1 = _relative_luminance(r1, g1, b1)
    l2 = _relative_luminance(r2, g2, b2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def verify_theme_contrast(theme: Theme) -> Dict[str, float]:
    """Validates that all foreground tokens satisfy WCAG AA contrast (>4.5:1)."""
    results = {
        "text_on_window": calculate_contrast_ratio(theme.text_color, theme.window_bg),
        "add_text_on_window": calculate_contrast_ratio(theme.add_text, theme.window_bg),
        "del_text_on_window": calculate_contrast_ratio(theme.del_text, theme.window_bg),
        "line_number_on_window": calculate_contrast_ratio(theme.line_number_color, theme.window_bg),
        "comment_on_window": calculate_contrast_ratio(theme.comment_color, theme.window_bg),
        "pill_text_on_pill_bg": calculate_contrast_ratio(theme.pill_text, theme.pill_bg),
    }

    for token, ratio in results.items():
        if ratio < 4.5:
            raise ValueError(
                f"Theme '{theme.name}' fails WCAG AA on token '{token}': "
                f"ratio {ratio:.2f}:1 is below 4.5:1 required."
            )
    return results