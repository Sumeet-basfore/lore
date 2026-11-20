"""2-Stage Hybrid Anti-Slop Humanization Engine.

Pass 1: Instant deterministic regex scrubbing (<1ms, zero LLM latency)
Pass 2: Voice & soul rhythm calibration and adversarial self-audit
"""

import math
import re
from typing import Any, Dict, List, Optional, Tuple

from lore.core.models import LoreConfig

# Prohibited AI words that immediately reveal machine-generated text
AI_VOCABULARY = [
    r"\bdelve\b",
    r"\bdelves\b",
    r"\bdelving\b",
    r"\btapestry\b",
    r"\btapestries\b",
    r"\btestament\b",
    r"\btestaments\b",
    r"\bpivotal\b",
    r"\bintricate\b",
    r"\bintricacies\b",
    r"\bcrucial\b",
    r"\blandscape\b",
    r"\blandscapes\b",
    r"\bvibrant\b",
    r"\bfostering\b",
    r"\bfosters\b",
    r"\bfoster\b",
    r"\bunderscoring\b",
    r"\bunderscores\b",
    r"\bunderscore\b",
    r"\bseamless\b",
    r"\bseamlessly\b",
    r"\bgroundbreaking\b",
    r"\brevolutionary\b",
    r"\bgame-changer\b",
    r"\bgame changer\b",
    r"\bleverage\b",
    r"\bleverages\b",
    r"\bleveraging\b",
    r"\butilize\b",
    r"\butilizes\b",
    r"\butilizing\b",
    r"\bfacilitate\b",
    r"\bfacilitates\b",
    r"\bfacilitating\b",
    r"\binterplay\b",
    r"\bmoreover\b",
    r"\bfurthermore\b",
    r"\badditionally\b",
    r"\beffortlessly\b",
    r"\bempower\b",
    r"\bempowering\b",
    r"\btransformative\b",
]

VOCAB_REPLACEMENTS = [
    (r"\butilize\b", "use"),
    (r"\butilizes\b", "uses"),
    (r"\butilizing\b", "using"),
    (r"\bleverage\b", "use"),
    (r"\bleverages\b", "uses"),
    (r"\bleveraging\b", "using"),
    (r"\bfacilitate\b", "help"),
    (r"\bfacilitates\b", "helps"),
    (r"\bfacilitating\b", "helping"),
    (r"\bdelve into\b", "inspect"),
    (r"\bdelves into\b", "inspects"),
    (r"\bdelving into\b", "inspecting"),
    (r"\bcrucial\b", "key"),
    (r"\bpivotal\b", "key"),
    (r"\bin order to\b", "to"),
    (r"\bdue to the fact that\b", "because"),
    (r"\bat this point in time\b", "now"),
    (r"\bit is important to note that\b", ""),
    (r"\bit should be noted that\b", ""),
]

COPULA_REPLACEMENTS = [
    (r"\bserves as a\b", "is a"),
    (r"\bserves as an\b", "is an"),
    (r"\bserves as\b", "is"),
    (r"\bstands as a\b", "is a"),
    (r"\bstands as an\b", "is an"),
    (r"\bstands as\b", "is"),
    (r"\bboasts a\b", "has a"),
    (r"\bboasts an\b", "has an"),
    (r"\bfeatures a\b", "has a"),
    (r"\bfunctions as a\b", "is a"),
    (r"\bfunctions as\b", "is"),
    (r"\bmarks a pivotal moment\b", "is a milestone"),
]

CHATBOT_PREFIXES = [
    r"^here is (the|a|an) (post|tweet|article|summary|changelog)?:?\s*",
    r"^certainly!?\s*",
    r"^sure!?\s*",
    r"^of course!?\s*",
    r"^i hope this helps!?\s*",
    r"^let's dive in!?\s*",
    r"^without further ado,?\s*",
    r"^here's what you need to know:?\s*",
    r"^great question!?\s*",
]

FORMULAIC_CLOSING_QUESTIONS = [
    r"(?i)\bwhat do you think\??(?:\s*👇)?",
    r"(?i)\blet me know (?:what you think|in the comments|below)\.?",
    r"(?i)\bhave you faced this before\??",
    r"(?i)\bshare your thoughts below\.?",
    r"(?i)\bwhat are your thoughts\??",
]

DECORATIVE_EMOJIS = ["🚀", "💡", "✅", "🔥", "✨", "📌", "🎉", "🌟"]


class Humanizer:
    """2-Stage Hybrid Anti-Slop Humanizer that enforces authentic engineering voice."""

    @classmethod
    def humanize(
        cls,
        text: str,
        config: Optional[LoreConfig] = None,
        voice_context: Optional[str] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """Maintains exact return signature: Tuple[str, Dict[str, Any]]."""
        # If voice_context was passed as second positional argument in older tests
        if isinstance(config, str) and voice_context is None:
            voice_context = config
            config = None

        audit_log: Dict[str, Any] = {
            "patterns_cleansed": [],
            "puffs_removed": 0,
            "em_dashes_replaced": 0,
            "chatbot_prefixes_removed": 0,
            "closing_questions_removed": 0,
            "copula_fixed": 0,
            "sentence_length_std_dev": 0.0,
        }

        # Stage 1: Deterministic Scrubbing Pass (<1ms)
        p1_text, audit_log = cls._deterministic_scrub(text, audit_log)

        # Stage 2: Voice & Soul rhythm calibration
        p2_text, audit_log = cls._calibrate_rhythm(p1_text, voice_context, audit_log)

        return p2_text.strip(), audit_log

    @classmethod
    def _deterministic_scrub(cls, text: str, audit: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        cleaned = text

        # 1. Strip chatbot preamble
        for pattern in CHATBOT_PREFIXES:
            if re.search(pattern, cleaned, re.IGNORECASE):
                cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()
                audit["chatbot_prefixes_removed"] += 1
                audit["patterns_cleansed"].append("chatbot_preamble")

        # 2. Normalize quotes
        cleaned = cleaned.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")

        # 3. Strip em-dashes
        em_dash_count = cleaned.count("—") + cleaned.count("--")
        if em_dash_count > 0:
            cleaned = re.sub(r"\s*—\s*", ", ", cleaned)
            cleaned = re.sub(r"\s*--\s*", ", ", cleaned)
            audit["em_dashes_replaced"] += em_dash_count
            audit["patterns_cleansed"].append("em_dash_crutch")

        # 4. Remove decorative emojis
        for emoji in DECORATIVE_EMOJIS:
            if emoji in cleaned:
                cleaned = cleaned.replace(emoji, "").strip()
                audit["patterns_cleansed"].append("decorative_emoji")

        # 5. Fix copula avoidance
        for pattern, replacement in COPULA_REPLACEMENTS:
            if re.search(pattern, cleaned, re.IGNORECASE):
                cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
                audit["copula_fixed"] += 1
                audit["patterns_cleansed"].append(f"copula:{replacement}")

        # 6. Replace corporate vocab
        for pattern, replacement in VOCAB_REPLACEMENTS:
            if re.search(pattern, cleaned, re.IGNORECASE):
                cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
                audit["patterns_cleansed"].append(f"vocab:{pattern}")

        # 7. Strip negative parallelism ("It's not just X, it's Y" -> "Y")
        neg_par = re.search(r"it's not (just|merely) about [^,]+,\s*(it's about|it's) ([^.]+)\.", cleaned, re.IGNORECASE)
        if neg_par:
            cleaned = re.sub(
                r"it's not (just|merely) about [^,]+,\s*(it's about|it's) ([^.]+)\.",
                r"\3.",
                cleaned,
                flags=re.IGNORECASE,
            )
            audit["patterns_cleansed"].append("negative_parallelism")

        # 8. Strip formulaic closing questions
        for pattern in FORMULAIC_CLOSING_QUESTIONS:
            if re.search(pattern, cleaned):
                cleaned = re.sub(pattern, "", cleaned).strip()
                audit["closing_questions_removed"] += 1
                audit["patterns_cleansed"].append("formulaic_closing_question")

        # 9. Scrub 35+ forbidden AI words
        for ai_word_pattern in AI_VOCABULARY:
            matches = re.findall(ai_word_pattern, cleaned, re.IGNORECASE)
            if matches:
                cleaned = re.sub(ai_word_pattern, "", cleaned, flags=re.IGNORECASE)
                cleaned = re.sub(r"\s{2,}", " ", cleaned)
                audit["patterns_cleansed"].append(f"scrubbed_ai_word:{matches[0]}")

        # 10. Clean trailing chatbot signoffs
        signoffs = [
            r"let me know what you think!?$",
            r"what are your thoughts\?$",
            r"happy coding!?$",
            r"i hope this helps!?$",
        ]
        for s in signoffs:
            if re.search(s, cleaned, re.IGNORECASE):
                cleaned = re.sub(s, "", cleaned, flags=re.IGNORECASE).strip()
                audit["patterns_cleansed"].append("chatbot_signoff")

        # 11. Clean spaces before punctuation
        cleaned = re.sub(r"\s+([,.;!?])", r"\1", cleaned)

        return cleaned, audit

    @classmethod
    def _calibrate_rhythm(
        cls, text: str, voice_context: Optional[str], audit: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        lines = [line.rstrip() for line in text.splitlines()]
        refined_lines = []

        # Remove corporate puffery
        puffs = [
            r"\bin today's (rapidly\s+)?evolving (technological\s+)?landscape,?\s*",
            r"\ba testament to [^,.]+[.,]?",
            r"\bmarking a pivotal moment\b",
            r"\bsetting the stage for [^,.]+[.,]?",
            r"\bexcited to announce (that)?\s*",
            r"\bthrilled to share (that)?\s*",
        ]

        for line in lines:
            line_str = line.strip()
            if not line_str:
                refined_lines.append("")
                continue

            for puff in puffs:
                if re.search(puff, line_str, re.IGNORECASE):
                    line_str = re.sub(puff, "", line_str, flags=re.IGNORECASE).strip()
                    audit["puffs_removed"] += 1
                    audit["patterns_cleansed"].append("puffery")

            if line_str and line_str[0].islower() and not line_str.startswith("http"):
                line_str = line_str[0].upper() + line_str[1:]

            refined_lines.append(line_str)

        result = "\n".join(refined_lines)

        # Compute sentence length std dev
        sentences = re.split(r"[.!?]+", result)
        lengths = [len(s.split()) for s in sentences if s.strip()]
        if len(lengths) > 1:
            mean = sum(lengths) / len(lengths)
            variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
            audit["sentence_length_std_dev"] = round(math.sqrt(variance), 2)

        return result, audit
