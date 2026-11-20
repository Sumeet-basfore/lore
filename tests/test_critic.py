"""Tests for Hacker News Critic Pass evaluation gate."""

import pytest
from lore.core.models import EvidenceRecord
from lore.generation.critic import HNCriticGate


def test_hn_critic_gate_deterministic_mock():
    raw_draft = (
        "We shipped a blazing fast update that delivers 10x speedup across the board!\n\n"
        "What do you think? 👇"
    )
    report = HNCriticGate.critique(raw_draft, force_mock=True)

    assert report.fluff_detected is True
    assert len(report.unsubstantiated_claims) > 0
    assert "blazing fast" not in report.sanitized_copy.lower()
    assert "what do you think" not in report.sanitized_copy.lower()
    assert report.sanitized_copy.strip()


def test_hn_critic_gate_clean_technical_pass():
    clean_draft = "Added connection pooling to SQLite queries. Reduced p95 latency from 14ms to 3ms."
    evidence = EvidenceRecord(insertions=40, deletions=10)
    report = HNCriticGate.critique(clean_draft, evidence=evidence, force_mock=True)

    assert len(report.unsubstantiated_claims) == 0
    assert "SQLite" in report.sanitized_copy
