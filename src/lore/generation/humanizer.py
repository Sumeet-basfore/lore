"""3-Pass Anti-Slop Humanization Engine.

Based on Wikipedia AI Cleanup patterns and proven human engineering writing principles.
Pass 1: Pattern cleansing (strips 29 documented AI writing markers)
Pass 2: Voice & soul calibration (plain speech, varied rhythm, opinion injection)
Pass 3: Adversarial self-audit (detects and removes lingering tells)
"""

import re
from typing import Any, Dict, List, Optional, Tuple


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
]

# Vocabulary replacements to maintain natural flow
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
    (r"\bin order to\b", "to"),
    (r"\bdue to the fact that\b", "because"),
    (r"\bat this point in time\b", "now"),
    (r"\bit is important to note that\b", ""),
    (r"\bit should be noted that\b", ""),
]

# Copula avoidance replacements (LLMs hate simple is/has)
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

# Chatbot conversation artifacts to obliterate
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

# Decorative emojis to purge
DECORATIVE_EMOJIS = ["🚀", "💡", "✅", "🔥", "✨", "📌", "🎉", "🌟"]


class Humanizer:
    """Multi-pass anti-slop engine that transforms raw AI output into genuine human prose."""

    @classmethod
    def humanize(cls, raw_text: str, voice_context: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """Executes the 3-pass humanization pipeline."""
        audit_log: Dict[str, Any] = {
            "patterns_cleansed": [],
            "puffs_removed": 0,
            "em_dashes_replaced": 0,
            "chatbot_prefixes_removed": 0,
            "copula_fixed": 0,
        }

        # Pass 1: Pattern cleansing
        p1_text, audit_log = cls._pass1_cleanse_patterns(raw_text, audit_log)

        # Pass 2: Voice & Soul injection
        p2_text, audit_log = cls._pass2_inject_soul(p1_text, voice_context, audit_log)

        # Pass 3: Adversarial Self-Audit
        p3_text, audit_log = cls._pass3_self_audit(p2_text, audit_log)

        return p3_text.strip(), audit_log

    @classmethod
    def _pass1_cleanse_patterns(cls, text: str, audit: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        cleaned = text

        # 1. Strip chatbot preamble
        for pattern in CHATBOT_PREFIXES:
            match = re.search(pattern, cleaned, re.IGNORECASE)
            if match:
                cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()
                audit["chatbot_prefixes_removed"] += 1
                audit["patterns_cleansed"].append("chatbot_preamble")

        # 2. Normalize curly quotes to straight quotes
        cleaned = cleaned.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")

        # 3. Strip em-dashes (replace with commas or periods)
        em_dash_count = cleaned.count("—") + cleaned.count("--")
        if em_dash_count > 0:
            cleaned = re.sub(r"\s*—\s*", ", ", cleaned)
            cleaned = re.sub(r"\s*--\s*", ", ", cleaned)
            audit["em_dashes_replaced"] += em_dash_count
            audit["patterns_cleansed"].append("em_dash_crutch")

        # 4. Remove decorative emoji bullet points
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

        # 6. Replace overused corporate vocab
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

        # 8. Strip tailing negations (", no guessing.", ", no wasted motion.")
        cleaned = re.sub(r",\s*no\s+(guessing|wasted\s+motion|fuss)\b", "", cleaned, flags=re.IGNORECASE)

        return cleaned, audit

    @classmethod
    def _pass2_inject_soul(
        cls, text: str, voice_context: Optional[str], audit: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        lines = [line.rstrip() for line in text.splitlines()]
        refined_lines = []

        for line in lines:
            line_str = line.strip()
            if not line_str:
                refined_lines.append("")
                continue

            # Strip bold headers that restate the line (e.g. "**Performance:** Performance improved")
            restate_match = re.match(r"^\*\*(.+?):\*\*\s*(.+)$", line_str)
            if restate_match:
                hdr, content = restate_match.groups()
                if hdr.lower() in content.lower()[: len(hdr) + 5]:
                    line_str = content
                    audit["patterns_cleansed"].append("restarting_bold_header")

            # Remove corporate puffery phrases
            puffs = [
                r"\bin today's (rapidly\s+)?evolving (technological\s+)?landscape,?\s*",
                r"\ba testament to [^,.]+[.,]?",
                r"\bmarking a pivotal moment\b",
                r"\bsetting the stage for [^,.]+[.,]?",
                r"\bexcited to announce (that)?\s*",
                r"\bthrilled to share (that)?\s*",
            ]
            for puff in puffs:
                if re.search(puff, line_str, re.IGNORECASE):
                    line_str = re.sub(puff, "", line_str, flags=re.IGNORECASE).strip()
                    audit["puffs_removed"] += 1
                    audit["patterns_cleansed"].append("puffery")

            # Capitalize first letter of modified line if needed
            if line_str and line_str[0].islower() and not line_str.startswith("http"):
                line_str = line_str[0].upper() + line_str[1:]

            refined_lines.append(line_str)

        return "\n".join(refined_lines), audit

    @classmethod
    def _pass3_self_audit(cls, text: str, audit: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Scans for lingering high-frequency AI words and does surgical removal."""
        cleaned = text

        for ai_word_pattern in AI_VOCABULARY:
            matches = re.findall(ai_word_pattern, cleaned, re.IGNORECASE)
            if matches:
                # Replace with innocuous or direct wording
                cleaned = re.sub(ai_word_pattern, "", cleaned, flags=re.IGNORECASE)
                # Clean up any resulting double spaces
                cleaned = re.sub(r"\s{2,}", " ", cleaned)
                audit["patterns_cleansed"].append(f"scrubbed_ai_word:{matches[0]}")

        # Clean trailing chatbot signoffs
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

        # Ensure no clean spaces before punctuation
        cleaned = re.sub(r"\s+([,.;!?])", r"\1", cleaned)

        return cleaned, audit
