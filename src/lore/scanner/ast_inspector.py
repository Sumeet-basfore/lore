"""AST Structural Code Inspector for Python, TypeScript/JavaScript, Rust, and Go."""

import ast
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from lore.core.models import ASTDiffReport
from lore.scanner.filters import is_noise_file


class ASTInspector:
    """Inspects diffs and source files to extract semantic structural changes."""

    @classmethod
    def inspect_diff_changes(
        cls,
        repo_path: Path,
        changed_files: List[str],
        diff_text: str = "",
    ) -> ASTDiffReport:
        repo_path = Path(repo_path)
        hero_file = cls.select_hero_file(changed_files)

        modified_classes: Set[str] = set()
        modified_functions: Set[str] = set()
        schema_migrations: Set[str] = set()
        inline_comments: List[str] = []
        test_assertions: List[str] = []

        # Parse diff line numbers per file
        diff_lines_per_file = cls._parse_diff_added_lines(diff_text)

        for rel_file in changed_files:
            if is_noise_file(rel_file):
                continue

            full_path = repo_path / rel_file
            ext = full_path.suffix.lower()
            added_lines = diff_lines_per_file.get(rel_file, [])

            # Check if file is a migration
            if "migration" in rel_file.lower() or "migrate" in rel_file.lower():
                schema_migrations.add(rel_file)

            if ext == ".py":
                cls._inspect_python_file(
                    full_path,
                    added_lines,
                    modified_classes,
                    modified_functions,
                    schema_migrations,
                    inline_comments,
                    test_assertions,
                )
            elif ext in [".ts", ".tsx", ".js", ".jsx"]:
                cls._inspect_ts_js_file(
                    full_path,
                    added_lines,
                    modified_classes,
                    modified_functions,
                    schema_migrations,
                    inline_comments,
                    test_assertions,
                )
            elif ext in [".rs", ".go"]:
                cls._inspect_compiled_lang_file(
                    full_path,
                    added_lines,
                    modified_classes,
                    modified_functions,
                    schema_migrations,
                    inline_comments,
                    test_assertions,
                )

        # Synthesize summary
        summary_parts = []
        if modified_classes:
            classes_str = ", ".join(sorted(list(modified_classes))[:3])
            summary_parts.append(f"Updated classes: {classes_str}")
        if modified_functions:
            funcs_str = ", ".join(sorted(list(modified_functions))[:4])
            summary_parts.append(f"Modified functions: {funcs_str}")
        if schema_migrations:
            summary_parts.append(f"Schema migrations in {len(schema_migrations)} file(s)")
        if test_assertions:
            assertions_str = "; ".join(test_assertions[:2])
            summary_parts.append(f"Verified behavior: {assertions_str}")

        synthesized_summary = ". ".join(summary_parts) if summary_parts else None

        return ASTDiffReport(
            hero_file=hero_file,
            modified_classes=sorted(list(modified_classes)),
            modified_functions=sorted(list(modified_functions)),
            schema_migrations=sorted(list(schema_migrations)),
            inline_comments=inline_comments[:10],
            test_assertions=test_assertions[:10],
            synthesized_summary=synthesized_summary,
        )

    @classmethod
    def select_hero_file(cls, changed_files: List[str]) -> Optional[str]:
        """Selects the primary non-lockfile domain file as the visual card hero."""
        candidates = [f for f in changed_files if not is_noise_file(f)]
        if not candidates:
            return changed_files[0] if changed_files else None

        # Prioritize core business logic, routers, models, handlers over tests or configs
        def score_file(path_str: str) -> int:
            s = 10
            lower = path_str.lower()
            if "test" in lower:
                s -= 5
            if "doc" in lower or lower.endswith(".md"):
                s -= 4
            if "core" in lower or "engine" in lower or "model" in lower or "service" in lower:
                s += 6
            if "api" in lower or "route" in lower or "view" in lower or "controller" in lower:
                s += 4
            if lower.endswith((".py", ".ts", ".tsx", ".rs", ".go")):
                s += 3
            return s

        candidates.sort(key=score_file, reverse=True)
        return candidates[0]

    @classmethod
    def _parse_diff_added_lines(cls, diff_text: str) -> Dict[str, List[int]]:
        """Parses unified diff to find added/modified line numbers per file."""
        lines_per_file: Dict[str, List[int]] = {}
        current_file = None
        current_line = 0

        for line in diff_text.splitlines():
            if line.startswith("+++ b/"):
                current_file = line[6:].strip()
                lines_per_file[current_file] = []
            elif line.startswith("@@ ") and current_file:
                # Format: @@ -old,count +new,count @@
                m = re.search(r"\+(\d+)(?:,(\d+))?", line)
                if m:
                    current_line = int(m.group(1))
            elif current_file and current_line > 0:
                if line.startswith("+") and not line.startswith("+++"):
                    lines_per_file[current_file].append(current_line)
                    current_line += 1
                elif line.startswith("-") and not line.startswith("---"):
                    pass
                else:
                    current_line += 1

        return lines_per_file

    @classmethod
    def _inspect_python_file(
        cls,
        path: Path,
        added_lines: List[int],
        modified_classes: Set[str],
        modified_functions: Set[str],
        schema_migrations: Set[str],
        inline_comments: List[str],
        test_assertions: List[str],
    ) -> None:
        if not path.is_file():
            return
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(content, filename=str(path))
        except Exception:
            return

        added_set = set(added_lines)

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                end_lineno = getattr(node, "end_lineno", node.lineno)
                if not added_set or any(node.lineno <= l <= end_lineno for l in added_set):
                    modified_classes.add(node.name)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end_lineno = getattr(node, "end_lineno", node.lineno)
                if not added_set or any(node.lineno <= l <= end_lineno for l in added_set):
                    modified_functions.add(node.name)
            elif isinstance(node, ast.Assert):
                end_lineno = getattr(node, "end_lineno", node.lineno)
                if not added_set or any(node.lineno <= l <= end_lineno for l in added_set):
                    try:
                        assertion_code = ast.unparse(node.test)
                        test_assertions.append(assertion_code)
                    except Exception:
                        pass

        # Extract comments and assert statements
        for idx, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#") and len(stripped) > 3 and not stripped.startswith("#!"):
                if not added_set or idx in added_set:
                    inline_comments.append(stripped.lstrip("#").strip())
            elif stripped.startswith("assert "):
                if not added_set or idx in added_set or len(modified_functions) > 0:
                    assertion_expr = stripped[7:].split(",")[0].strip()
                    if assertion_expr and assertion_expr not in test_assertions:
                        test_assertions.append(assertion_expr)

    @classmethod
    def _inspect_ts_js_file(
        cls,
        path: Path,
        added_lines: List[int],
        modified_classes: Set[str],
        modified_functions: Set[str],
        schema_migrations: Set[str],
        inline_comments: List[str],
        test_assertions: List[str],
    ) -> None:
        if not path.is_file():
            return
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return

        added_set = set(added_lines)
        for idx, line in enumerate(content.splitlines(), start=1):
            if added_set and idx not in added_set:
                continue

            stripped = line.strip()
            # Comments
            if stripped.startswith("//") and len(stripped) > 3:
                inline_comments.append(stripped.lstrip("/").strip())

            # Classes
            m_class = re.search(r"(?:export\s+)?class\s+([A-Za-z0-9_]+)", stripped)
            if m_class:
                modified_classes.add(m_class.group(1))

            # Functions
            m_fn = re.search(r"(?:export\s+)?(?:async\s+)?function\s+([A-Za-z0-9_]+)", stripped)
            if m_fn:
                modified_functions.add(m_fn.group(1))
            m_arrow = re.search(r"(?:export\s+)?const\s+([A-Za-z0-9_]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>", stripped)
            if m_arrow:
                modified_functions.add(m_arrow.group(1))

            # Test assertions: expect(...)
            m_assert = re.search(r"(expect\([^)]+\)\.[A-Za-z0-9_]+(?:\([^)]*\))?)", stripped)
            if m_assert:
                test_assertions.append(m_assert.group(1))

    @classmethod
    def _inspect_compiled_lang_file(
        cls,
        path: Path,
        added_lines: List[int],
        modified_classes: Set[str],
        modified_functions: Set[str],
        schema_migrations: Set[str],
        inline_comments: List[str],
        test_assertions: List[str],
    ) -> None:
        if not path.is_file():
            return
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return

        added_set = set(added_lines)
        for idx, line in enumerate(content.splitlines(), start=1):
            if added_set and idx not in added_set:
                continue

            stripped = line.strip()
            if stripped.startswith("//") and len(stripped) > 3:
                inline_comments.append(stripped.lstrip("/").strip())

            # Rust structs / Go structs
            m_struct = re.search(r"(?:pub\s+)?(?:struct|type)\s+([A-Za-z0-9_]+)", stripped)
            if m_struct:
                modified_classes.add(m_struct.group(1))

            # Rust fn / Go func
            m_fn = re.search(r"(?:pub\s+)?(?:async\s+)?fn\s+([A-Za-z0-9_]+)", stripped)
            if m_fn:
                modified_functions.add(m_fn.group(1))
            m_gofn = re.search(r"func\s+(?:\([^)]+\)\s+)?([A-Za-z0-9_]+)\s*\(", stripped)
            if m_gofn:
                modified_functions.add(m_gofn.group(1))

            # Assertions
            m_assert = re.search(r"(assert(?:_eq)?!\([^)]+\))", stripped)
            if m_assert:
                test_assertions.append(m_assert.group(1))
