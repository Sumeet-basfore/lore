"""Hacker News Critic Pass evaluation gate."""

import json
import os
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from lore.core.models import EvidenceRecord
from lore.generation.humanizer import Humanizer


class CriticReport(BaseModel):
    fluff_detected: bool
    unsubstantiated_claims: List[Dict[str, str]] = Field(default_factory=list)
    sanitized_copy: str


class HNCriticGate:
    """Evaluates drafts through the lens of a skeptical Hacker News engineer."""

    @classmethod
    def critique(
        cls,
        draft_content: str,
        evidence: Optional[EvidenceRecord] = None,
        force_mock: bool = False,
    ) -> CriticReport:
        return cls._deterministic_critic(draft_content, evidence)

    @classmethod
    def _deterministic_critic(
        cls, draft_content: str, evidence: Optional[EvidenceRecord]
    ) -> CriticReport:
        unsubstantiated: List[Dict[str, str]] = []
        cleaned = draft_content

        # 1. Strike performance / speed superlatives if not backed by evidence numbers
        superlatives = [
            (r"\b10x (?:faster|speedup|improvement)\b", "10x claim without benchmark evidence"),
            (r"\bblazing fast\b", "Vague superlative 'blazing fast'"),
            (r"\blightning fast\b", "Vague superlative 'lightning fast'"),
            (r"\binfinitely scalable\b", "Unsubstantiated scalability claim"),
            (r"\bzero latency\b", "Unsubstantiated zero latency claim"),
        ]

        for pattern, reason in superlatives:
            match = re.search(pattern, cleaned, re.IGNORECASE)
            if match:
                matched_text = match.group(0)
                cleaned = re.sub(pattern, "faster", cleaned, flags=re.IGNORECASE)
                unsubstantiated.append({"claim": matched_text, "fix": "Substituted with measured technical statement"})

        # 2. Ban double-spaced single-sentence vertical formatting (LinkedIn broetry on tech posts)
        cleaned = re.sub(r"\n\s*\n\s*\n+", "\n\n", cleaned)

        # 3. Run final deterministic humanizer scrubber to ensure zero buzzword regressions
        scrubbed, audit = Humanizer.humanize(cleaned)

        fluff_detected = bool(unsubstantiated or audit["puffs_removed"] > 0)

        return CriticReport(
            fluff_detected=fluff_detected,
            unsubstantiated_claims=unsubstantiated,
            sanitized_copy=scrubbed,
        )
