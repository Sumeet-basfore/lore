"""Tests for AST Structural Code Inspection and High-Entropy Diff Ingestion."""

import tempfile
from pathlib import Path
from lore.scanner.ast_inspector import ASTInspector
from lore.core.models import ASTDiffReport


def test_ast_inspector_python():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        py_file = tmp_path / "service.py"
        py_file.write_text(
            """# In-memory fast cache implementation
class CacheManager:
    def get_value(self, key: str):
        # Retrieve key directly
        assert key is not None
        return True
""",
            encoding="utf-8",
        )

        diff_text = """--- a/service.py
+++ b/service.py
@@ -1,6 +1,6 @@
+# In-memory fast cache implementation
 class CacheManager:
+    def get_value(self, key: str):
+        assert key is not None
"""
        report: ASTDiffReport = ASTInspector.inspect_diff_changes(
            tmp_path,
            ["service.py"],
            diff_text,
        )

        assert report.hero_file == "service.py"
        assert "CacheManager" in report.modified_classes
        assert "get_value" in report.modified_functions
        assert len(report.inline_comments) > 0
        assert any("cache" in c.lower() for c in report.inline_comments)
        assert len(report.test_assertions) > 0
        assert report.synthesized_summary is not None


def test_ast_inspector_hero_file_selection():
    files = ["poetry.lock", "package-lock.json", "tests/test_auth.py", "src/auth/service.py"]
    hero = ASTInspector.select_hero_file(files)
    assert hero == "src/auth/service.py"


def test_ast_inspector_ts_and_assertions():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        ts_file = tmp_path / "auth.ts"
        ts_file.write_text(
            """// Modern JWT validation helper
export class JWTValidator {
    validateToken(token: string) {
        expect(token).toBeDefined();
        return true;
    }
}
""",
            encoding="utf-8",
        )

        diff_text = """--- a/auth.ts
+++ b/auth.ts
@@ -1,3 +1,5 @@
+// Modern JWT validation helper
+export class JWTValidator {
+    validateToken(token: string) {
"""
        report: ASTDiffReport = ASTInspector.inspect_diff_changes(
            tmp_path,
            ["auth.ts"],
            diff_text,
        )

        assert "JWTValidator" in report.modified_classes
        assert len(report.inline_comments) > 0
        assert any("jwt" in c.lower() for c in report.inline_comments)
