"""Unit tests for Enterprise DLP & Shannon Entropy Engine."""

import pytest
from lore.security.dlp_scanner import DLPScanner, DLPViolationError
from lore.security.entropy import calculate_shannon_entropy, scan_text_entropy, verify_git_sha
from lore.security.masks import mask_ast_loops, mask_custom_entities


def test_shannon_entropy_calculation():
    # Low entropy repeating strings
    assert calculate_shannon_entropy("aaaaaaaaaaaa") < 1.0
    # High entropy base64 string
    assert calculate_shannon_entropy("dGhpcy1pcy1hLWhpZ2gtZW50cm9weS1zZWNyZXQtdmFsdWU=") >= 4.5


def test_dlp_tier1_hard_block_aws():
    text_with_aws = "We configured credentials with AKIAIOSFODNN7EXAMPLE for deployment."
    res = DLPScanner.scan(text_with_aws)
    assert res.status == "BLOCKED"
    assert res.clean_text == "[CONTENT_DROPPED_DUE_TO_DLP_VIOLATION]"
    assert any("AWS Access Key ID" in v["description"] for v in res.violations)


def test_dlp_tier1_hard_block_openai():
    text_with_openai = 'const key = "sk-proj-abc1234567890abcdefghijklmnopqrstuvwxyz";'
    res = DLPScanner.scan(text_with_openai)
    assert res.status == "BLOCKED"


def test_dlp_tier2_mask_staging_domain():
    text_with_internal = "Testing endpoints at api.staging.example.com and internal host db.internal."
    res = DLPScanner.scan(text_with_internal)
    assert res.status == "REDACTED"
    assert "api.staging.example.com" not in res.clean_text
    assert "[MASKED_STAGING_HOST]" in res.clean_text
    assert "[MASKED_INTERNAL_HOST]" in res.clean_text


def test_git_sha_verification_whitelist():
    # Synthetic SHA that does not exist in any local repo
    fake_sha = "e" * 40
    assert verify_git_sha(fake_sha, known_shas={"1" * 40}) is False
    assert verify_git_sha("1" * 40, known_shas={"1" * 40}) is True


def test_redos_safety_long_line():
    long_line = "a" * 5000
    # Should evaluate and skip long lines cleanly without hanging
    res = DLPScanner.scan(long_line)
    assert res.status == "PASSED"


def test_ast_loop_masking():
    py_code = """
def run_computation(items):
    total = 0
    for item in items:
        # Complex proprietary trade secret loop
        temp = item * 42
        total += temp
    return total
"""
    masked = mask_ast_loops(py_code, file_type="py")
    assert "[proprietary implementation hidden]" in masked
    assert "temp = item * 42" not in masked
