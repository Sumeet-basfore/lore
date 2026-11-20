"""AST Diff Truncator & Code Normalizer.

Prepares git diffs for high-contrast visual cards:
- Strictly enforces hard-wrap ban (max 84 cols, truncating with ellipsis).
- Collapses unchanged context lines into semantic ellipsis (// ...).
- Intelligently prioritizes addition/deletion hunks within card line limits.
- Gracefully handles empty and binary diffs with structured metadata badges.
"""

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Optional


@dataclass
class DiffLine:
    """Represents a formatted single line in a visual diff card."""
    line_type: str  # "add", "del", "context", "collapse", "header"
    content: str
    old_lineno: Optional[int] = None
    new_lineno: Optional[int] = None


@dataclass
class FormattedDiff:
    """Structured diff representation ready for visual layout rendering."""
    lines: List[DiffLine] = field(default_factory=list)
    file_path: Optional[str] = None
    insertions: int = 0
    deletions: int = 0
    is_empty_or_binary: bool = False
    summary: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


def truncate_diff_for_card(
    diff_text: str,
    max_lines: int = 14,
    max_cols: int = 84,
    file_label: Optional[str] = None,
) -> FormattedDiff:
    """Truncates and normalizes git diff text for deterministic card rendering.

    Args:
        diff_text: Raw diff string from git.
        max_lines: Maximum code lines to display (14 for 16:9, 20 for 1:1).
        max_cols: Maximum characters per line before hard truncation.
        file_label: Optional filename override.

    Returns:
        FormattedDiff object ready for SVG rendering.
    """
    raw_text = (diff_text or "").strip()

    # 1. Handle empty diff
    if not raw_text:
        return FormattedDiff(
            lines=[
                DiffLine(
                    line_type="header",
                    content="// No diff changes recorded",
                ),
                DiffLine(
                    line_type="context",
                    content="// Working tree matches repository HEAD",
                ),
            ],
            file_path=file_label or "README.md",
            insertions=0,
            deletions=0,
            is_empty_or_binary=True,
            summary="Empty diff",
        )

    # 2. Handle binary diffs
    if "Binary files " in raw_text or "GIT binary patch" in raw_text:
        detected_file = file_label or _extract_file_path(raw_text) or "binary_asset"
        return FormattedDiff(
            lines=[
                DiffLine(
                    line_type="header",
                    content=f"// Binary file modified: {detected_file}",
                ),
                DiffLine(
                    line_type="context",
                    content="// Binary diff content omitted from text card",
                ),
            ],
            file_path=detected_file,
            insertions=0,
            deletions=0,
            is_empty_or_binary=True,
            summary=f"Binary asset update ({detected_file})",
        )

    # 3. Parse diff hunks and lines
    parsed_lines, extracted_file, ins_count, del_count = _parse_diff_lines(raw_text)
    final_file = file_label or extracted_file or "code_diff"

    if not parsed_lines:
        return FormattedDiff(
            lines=[
                DiffLine(line_type="header", content=f"// {final_file}"),
                DiffLine(line_type="context", content="// Metadata change only"),
            ],
            file_path=final_file,
            insertions=ins_count,
            deletions=del_count,
            is_empty_or_binary=True,
            summary=f"Metadata update on {final_file}",
        )

    # 4. Remove common leading whitespace among code lines
    normalized_lines = _strip_common_indentation(parsed_lines)

    # 5. Enforce line limit with semantic collapsing
    selected_lines = _collapse_and_fit(normalized_lines, max_lines=max_lines)

    # 6. Hard-wrap ban: truncate any line exceeding max_cols
    final_lines: List[DiffLine] = []
    for line in selected_lines:
        truncated_content = _truncate_line(line.content, max_cols=max_cols)
        final_lines.append(
            DiffLine(
                line_type=line.line_type,
                content=truncated_content,
                old_lineno=line.old_lineno,
                new_lineno=line.new_lineno,
            )
        )

    return FormattedDiff(
        lines=final_lines,
        file_path=final_file,
        insertions=ins_count,
        deletions=del_count,
        is_empty_or_binary=False,
        summary=f"{final_file}: +{ins_count}/-{del_count}",
    )


def _extract_file_path(diff_text: str) -> Optional[str]:
    """Extracts the modified target file path from a git diff header."""
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            return line[6:].strip()
        if line.startswith("diff --git a/"):
            parts = line.split(" b/")
            if len(parts) > 1:
                return parts[1].strip()
    return None


def _parse_diff_lines(diff_text: str):
    """Parses raw diff text into DiffLine items, tracking hunk line numbers."""
    lines: List[DiffLine] = []
    file_path = _extract_file_path(diff_text)
    insertions = 0
    deletions = 0

    old_line = 0
    new_line = 0
    hunk_regex = re.compile(r"^@@\s+-(\d+)(?:,\d+)?\s+\+(\d+)(?:,\d+)?\s+@@")

    for raw in diff_text.splitlines():
        if (
            raw.startswith("diff --git")
            or raw.startswith("index ")
            or raw.startswith("--- ")
            or raw.startswith("+++ ")
        ):
            continue

        hunk_match = hunk_regex.match(raw)
        if hunk_match:
            old_line = int(hunk_match.group(1))
            new_line = int(hunk_match.group(2))
            lines.append(DiffLine(line_type="collapse", content="// ..."))
            continue

        if not raw:
            continue

        marker = raw[0]
        content = raw[1:] if len(raw) > 1 else ""

        if marker == "+":
            insertions += 1
            lines.append(
                DiffLine(
                    line_type="add",
                    content=content,
                    old_lineno=None,
                    new_lineno=new_line,
                )
            )
            new_line += 1
        elif marker == "-":
            deletions += 1
            lines.append(
                DiffLine(
                    line_type="del",
                    content=content,
                    old_lineno=old_line,
                    new_lineno=None,
                )
            )
            old_line += 1
        elif marker == " ":
            lines.append(
                DiffLine(
                    line_type="context",
                    content=content,
                    old_lineno=old_line,
                    new_lineno=new_line,
                )
            )
            old_line += 1
            new_line += 1

    return lines, file_path, insertions, deletions


def _strip_common_indentation(lines: List[DiffLine]) -> List[DiffLine]:
    """Calculates and strips common leading spaces across non-empty code lines."""
    indent_candidates = []
    for line in lines:
        if line.line_type in ("add", "del", "context") and line.content.strip():
            leading = len(line.content) - len(line.content.lstrip(" "))
            indent_candidates.append(leading)

    if not indent_candidates:
        return lines

    min_indent = min(indent_candidates)
    if min_indent <= 0:
        return lines

    result = []
    for line in lines:
        if line.line_type in ("add", "del", "context") and len(line.content) >= min_indent:
            new_content = line.content[min_indent:]
        else:
            new_content = line.content
        result.append(
            DiffLine(
                line_type=line.line_type,
                content=new_content,
                old_lineno=line.old_lineno,
                new_lineno=line.new_lineno,
            )
        )
    return result


def _collapse_and_fit(lines: List[DiffLine], max_lines: int) -> List[DiffLine]:
    """Fits diff lines into max_lines by collapsing large blocks of context."""
    if len(lines) <= max_lines:
        return lines

    diff_indices = {i for i, line in enumerate(lines) if line.line_type in ("add", "del")}
    if not diff_indices:
        return lines[:max_lines]

    compacted: List[DiffLine] = []
    consecutive_context = 0
    for line in lines:
        if line.line_type == "context":
            consecutive_context += 1
            if consecutive_context <= 2:
                compacted.append(line)
            elif consecutive_context == 3:
                compacted.append(DiffLine(line_type="collapse", content="// ..."))
        else:
            consecutive_context = 0
            compacted.append(line)

    if len(compacted) <= max_lines:
        return compacted

    first_diff = min(i for i, line in enumerate(compacted) if line.line_type in ("add", "del"))
    start = max(0, first_diff - 1)
    end = min(len(compacted), start + max_lines)
    if (end - start) < max_lines and start > 0:
        start = max(0, end - max_lines)

    result = compacted[start:end]
    if start > 0 and result and result[0].line_type != "collapse":
        result[0] = DiffLine(line_type="collapse", content="// ...")
    if end < len(compacted) and result and result[-1].line_type != "collapse":
        result[-1] = DiffLine(line_type="collapse", content="// ...")

    return result[:max_lines]


def _truncate_line(content: str, max_cols: int) -> str:
    """Hard wrap ban: never wrap lines. Truncate at max_cols with '…'."""
    if len(content) <= max_cols:
        return content
    return content[: max_cols - 1] + "…"