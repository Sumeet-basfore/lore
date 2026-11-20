"""Custom entity masking and AST algorithmic loop redaction."""

import ast
import re
from typing import Dict, List, Tuple


def mask_custom_entities(
    text: str, custom_masks: List[Dict[str, str]]
) -> Tuple[str, List[str]]:
    """Applies custom regex redaction rules configured by the user in .lorerc.yaml."""
    masked_text = text
    applied: List[str] = []

    for item in custom_masks:
        pattern = item.get("pattern", "")
        replacement = item.get("replacement", "[MASKED]")
        if not pattern:
            continue
        try:
            if re.search(pattern, masked_text):
                masked_text = re.sub(pattern, replacement, masked_text)
                applied.append(pattern)
        except re.error:
            continue

    return masked_text, applied


def mask_ast_loops(source_code: str, file_type: str = "py") -> str:
    """Abstracts deep algorithmic loop bodies to prevent leaking proprietary trade secret logic."""
    if file_type == "py":
        try:
            tree = ast.parse(source_code)
            lines = source_code.splitlines()

            # Find For and While loops with deep or proprietary computation
            replacements: List[Tuple[int, int, int]] = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
                    if len(node.body) > 1:
                        first_line = node.body[0].lineno
                        last_line = node.body[-1].end_lineno or node.body[-1].lineno
                        indent = getattr(node.body[0], "col_offset", 4)
                        replacements.append((first_line, last_line, indent))

            # Apply replacements from bottom to top to preserve line numbering
            replacements.sort(key=lambda x: x[0], reverse=True)
            for start, end, col in replacements:
                indent_str = " " * col
                replacement_text = f"{indent_str}# ... [proprietary implementation hidden]"
                lines = lines[: start - 1] + [replacement_text] + lines[end:]

            return "\n".join(lines)
        except Exception:
            return source_code

    # Fallback regex masking for JS/TS/Rust
    masked = re.sub(
        r"(for\s*\([^)]*\)\s*\{)[^}]+(\})",
        r"\1\n    // ... [proprietary implementation hidden]\n\2",
        source_code,
    )
    return masked
