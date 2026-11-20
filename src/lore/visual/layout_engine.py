"""SVG layout engine for visual diff cards with macOS window styling."""

import html
from typing import Optional
from lore.visual.assets.fonts import FONT_STACK, get_typography_metrics
from lore.visual.ast_diff_truncator import FormattedDiff
from lore.visual.themes import Theme, get_theme


class CardLayout:
    """Calculates deterministic SVG layout and renders high-contrast diff cards."""

    def __init__(self, theme: Optional[Theme] = None, aspect_ratio: str = "16:9"):
        self.theme = theme or get_theme("tokyo_night")
        self.aspect_ratio = aspect_ratio
        self.metrics = get_typography_metrics(aspect_ratio)

    def render(self, diff: FormattedDiff, file_label: Optional[str] = None) -> str:
        """Renders FormattedDiff into a complete, standalone SVG document."""
        w = int(self.metrics["card_width"])
        h = int(self.metrics["card_height"])
        margin = self.metrics["window_margin"]
        header_h = self.metrics["header_height"]
        font_size = self.metrics["font_size"]
        line_height = self.metrics["line_height"]

        win_x = margin
        win_y = margin
        win_w = w - (2 * margin)
        win_h = h - (2 * margin)

        display_title = html.escape(file_label or diff.file_path or "diff")
        theme = self.theme

        traffic_y = win_y + (header_h / 2.0)
        close_x = win_x + 22
        min_x = close_x + 18
        max_x = min_x + 18

        pill_w = 110.0
        pill_h = 24.0
        pill_x = win_x + win_w - pill_w - 16.0
        pill_y = win_y + ((header_h - pill_h) / 2.0)

        svg_parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">',
            '  <defs>',
            '    <filter id="card-shadow" x="-5%" y="-5%" width="110%" height="110%">',
            '      <feDropShadow dx="0" dy="16" stdDeviation="24" flood-color="#000000" flood-opacity="0.45" />',
            '    </filter>',
            '  </defs>',
            '  <style>',
            f'    .code-text {{ font-family: {FONT_STACK}; font-size: {font_size}px; }}',
            f'    .title-text {{ font-family: {FONT_STACK}; font-size: 13px; font-weight: 500; fill: {theme.text_color}; }}',
            f'    .pill-text {{ font-family: {FONT_STACK}; font-size: 11px; font-weight: 600; fill: {theme.pill_text}; }}',
            f'    .lineno {{ font-family: {FONT_STACK}; font-size: {font_size - 4}px; fill: {theme.line_number_color}; text-anchor: end; }}',
            f'    .sign {{ font-family: {FONT_STACK}; font-size: {font_size}px; font-weight: bold; }}',
            '  </style>',
            f'  <rect width="{w}" height="{h}" fill="{theme.bg_color}" />',
            f'  <rect x="{win_x}" y="{win_y}" width="{win_w}" height="{win_h}" rx="12" fill="{theme.window_bg}" stroke="{theme.border_color}" stroke-width="1.5" filter="url(#card-shadow)" />',
            f'  <path d="M {win_x} {win_y + 12} A 12 12 0 0 1 {win_x + 12} {win_y} L {win_x + win_w - 12} {win_y} A 12 12 0 0 1 {win_x + win_w} {win_y + 12} L {win_x + win_w} {win_y + header_h} L {win_x} {win_y + header_h} Z" fill="{theme.header_bg}" />',
            f'  <line x1="{win_x}" y1="{win_y + header_h}" x2="{win_x + win_w}" y2="{win_y + header_h}" stroke="{theme.border_color}" stroke-width="1" />',
            f'  <circle cx="{close_x}" cy="{traffic_y}" r="6" fill="#FF5F56" />',
            f'  <circle cx="{min_x}" cy="{traffic_y}" r="6" fill="#FFBD2E" />',
            f'  <circle cx="{max_x}" cy="{traffic_y}" r="6" fill="#27C93F" />',
            f'  <text x="{win_x + (win_w / 2)}" y="{traffic_y + 4.5}" class="title-text" text-anchor="middle">{display_title}</text>',
            f'  <rect x="{pill_x}" y="{pill_y}" width="{pill_w}" height="{pill_h}" rx="6" fill="{theme.pill_bg}" />',
            f'  <text x="{pill_x + (pill_w / 2)}" y="{pill_y + 16}" class="pill-text" text-anchor="middle">lore.dev/diff</text>',
        ]

        start_y = win_y + header_h + 36.0
        lineno_col_x = win_x + 55.0
        sign_col_x = win_x + 75.0
        code_col_x = win_x + 98.0
        line_w = win_w - 2.0

        for i, line in enumerate(diff.lines):
            curr_y = start_y + (i * line_height)
            box_y = curr_y - (line_height * 0.75)

            if line.line_type == "add":
                svg_parts.append(
                    f'  <rect x="{win_x + 1}" y="{box_y}" width="{line_w}" height="{line_height}" fill="{theme.add_bg}" />'
                )
            elif line.line_type == "del":
                svg_parts.append(
                    f'  <rect x="{win_x + 1}" y="{box_y}" width="{line_w}" height="{line_height}" fill="{theme.del_bg}" />'
                )

            if line.line_type == "collapse":
                num_str = ""
            elif line.line_type == "del" and line.old_lineno is not None:
                num_str = str(line.old_lineno)
            elif line.new_lineno is not None:
                num_str = str(line.new_lineno)
            else:
                num_str = ""

            if num_str:
                svg_parts.append(
                    f'  <text x="{lineno_col_x}" y="{curr_y}" class="lineno">{num_str}</text>'
                )

            if line.line_type == "add":
                svg_parts.append(
                    f'  <text x="{sign_col_x}" y="{curr_y}" class="sign" fill="{theme.add_text}">+</text>'
                )
            elif line.line_type == "del":
                svg_parts.append(
                    f'  <text x="{sign_col_x}" y="{curr_y}" class="sign" fill="{theme.del_text}">-</text>'
                )

            escaped_code = html.escape(line.content)
            if line.line_type == "add":
                text_color = theme.add_text
            elif line.line_type == "del":
                text_color = theme.del_text
            elif line.line_type == "collapse":
                text_color = theme.comment_color
            else:
                text_color = theme.text_color

            font_style = ' font-style="italic"' if line.line_type == "collapse" else ""
            svg_parts.append(
                f'  <text x="{code_col_x}" y="{curr_y}" class="code-text" fill="{text_color}"{font_style}>{escaped_code}</text>'
            )

        if self.aspect_ratio == "1:1":
            bottom_h = self.metrics["bottom_bar_height"]
            bar_y = win_y + win_h - bottom_h
            svg_parts.extend([
                f'  <line x1="{win_x}" y1="{bar_y}" x2="{win_x + win_w}" y2="{bar_y}" stroke="{theme.border_color}" stroke-width="1" />',
                f'  <text x="{win_x + 30}" y="{bar_y + 35}" font-family="{FONT_STACK}" font-size="14" font-weight="bold" fill="{theme.add_text}">+{diff.insertions} LOC</text>',
                f'  <text x="{win_x + 130}" y="{bar_y + 35}" font-family="{FONT_STACK}" font-size="14" font-weight="bold" fill="{theme.del_text}">-{diff.deletions} LOC</text>',
                f'  <text x="{win_x + win_w - 30}" y="{bar_y + 35}" font-family="{FONT_STACK}" font-size="13" fill="{theme.comment_color}" text-anchor="end">{theme.display_name}</text>',
            ])

        svg_parts.append("</svg>")
        return "\n".join(svg_parts)


def render_diff_svg(
    diff: FormattedDiff,
    theme: Optional[Theme] = None,
    aspect_ratio: str = "16:9",
    file_label: Optional[str] = None,
) -> str:
    """Convenience helper to render SVG directly from a FormattedDiff."""
    layout = CardLayout(theme=theme, aspect_ratio=aspect_ratio)
    return layout.render(diff, file_label=file_label)