"""Voice profile calibration and author writing style analyzer."""

import re
from typing import Any, Dict, List
from lore.core.models import VoiceSample


class VoiceCalibrator:
    """Analyzes personal writing samples to extract cadence, tone, and stylistic habits."""

    @classmethod
    def analyze_sample(cls, text: str) -> Dict[str, Any]:
        clean_text = text.strip()
        if not clean_text:
            return {
                "avg_sentence_len": 12.0,
                "contraction_rate": 0.5,
                "first_person_rate": 0.5,
                "prefers_short_paragraphs": True,
            }

        # Split into sentences
        sentences = [s.strip() for s in re.split(r"[.!?]+", clean_text) if s.strip()]
        sentence_lengths = [len(s.split()) for s in sentences] if sentences else [10]
        avg_sentence_len = round(sum(sentence_lengths) / len(sentence_lengths), 1)

        # Contractions count
        words = clean_text.lower().split()
        contractions = [w for w in words if "'" in w or "’" in w]
        contraction_rate = round(len(contractions) / max(len(words), 1), 3)

        # First person pronouns count
        first_person_tokens = {"i", "me", "my", "mine", "we", "us", "our", "ours"}
        first_person_count = sum(1 for w in words if w.strip(".,!?;:\"'") in first_person_tokens)
        first_person_rate = round(first_person_count / max(len(words), 1), 3)

        # Paragraph analysis
        paragraphs = [p.strip() for p in clean_text.split("\n\n") if p.strip()]
        avg_para_len = round(sum(len(p.split()) for p in paragraphs) / max(len(paragraphs), 1), 1)

        return {
            "avg_sentence_len": avg_sentence_len,
            "sentence_count": len(sentences),
            "contraction_rate": contraction_rate,
            "first_person_rate": first_person_rate,
            "avg_paragraph_len": avg_para_len,
            "prefers_short_paragraphs": avg_para_len < 40,
        }

    @classmethod
    def build_voice_context(cls, samples: List[VoiceSample]) -> str:
        """Constructs prompt guidance for the LLM based on aggregate sample analysis."""
        if not samples:
            return (
                "Author style: Pragmatic, direct software engineer. "
                "Uses contractions ('we've', 'don't'), varies sentence length naturally, "
                "favors short 1-2 sentence paragraphs, and shares real engineering lessons."
            )

        total_words = 0
        total_sentences = 0
        total_first_person = 0

        for s in samples:
            analysis = s.analysis or cls.analyze_sample(s.content)
            total_sentences += analysis.get("sentence_count", 1)
            total_first_person += analysis.get("first_person_rate", 0.05)

        avg_fp = round(total_first_person / len(samples), 3)

        guidance = [
            "- Write in the author's real voice: conversational, candid, and technically grounded.",
            "- Use natural contractions (don't, we'll, it's, couldn't).",
            "- Use short, punchy paragraphs with clear visual breathing room.",
        ]

        if avg_fp > 0.03:
            guidance.append("- Use first-person perspective naturally ('I built', 'We ran', 'Here is what broke').")

        return "\n".join(guidance)
