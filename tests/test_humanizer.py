"""Tests for 3-Pass Anti-Slop Humanization Engine and Voice Calibration."""

from lore.core.models import VoiceSample
from lore.generation.humanizer import Humanizer
from lore.generation.voice import VoiceCalibrator


def test_humanizer_pass1_patterns():
    ai_raw = (
        "Here is the post: We are excited to announce our new feature—it serves as a testament "
        "to our ongoing journey. In today's rapidly evolving landscape, this groundbreaking tool "
        "leverages modern APIs in order to facilitate developer workflows. 🚀 Launch: Speed matters."
    )

    humanized, audit = Humanizer.humanize(ai_raw)

    # Chatbot preamble removed
    assert not humanized.lower().startswith("here is the post")

    # Em-dashes replaced
    assert "—" not in humanized

    # Decorative rocket emoji stripped
    assert "🚀" not in humanized

    # Copula avoidance fixed ("serves as a" replaced with "is a")
    assert "serves as a" not in humanized.lower()

    # AI vocabulary words stripped/replaced
    assert "testament" not in humanized.lower()
    assert "groundbreaking" not in humanized.lower()
    assert "leverage" not in humanized.lower()
    assert "facilitate" not in humanized.lower()
    assert "in today's rapidly evolving landscape" not in humanized.lower()

    assert len(audit["patterns_cleansed"]) > 0


def test_humanizer_negative_parallelism():
    raw = "It's not just about speed, it's about database reliability."
    humanized, audit = Humanizer.humanize(raw)
    assert "it's not just about" not in humanized.lower()
    assert "database reliability" in humanized.lower()


def test_humanizer_curly_quotes_and_signoff():
    raw = 'He said “the deploy succeeded”. Let me know what you think!'
    humanized, audit = Humanizer.humanize(raw)
    assert "“" not in humanized
    assert "”" not in humanized
    assert "Let me know what you think" not in humanized


def test_voice_calibrator():
    sample_text = (
        "We built a quick pipeline today. Didn't want to use Kafka because it's too heavy. "
        "SQLite handled 5,000 requests a second with zero configuration."
    )
    analysis = VoiceCalibrator.analyze_sample(sample_text)
    assert analysis["sentence_count"] >= 2
    assert analysis["contraction_rate"] > 0.0
    assert analysis["prefers_short_paragraphs"] is True

    samples = [
        VoiceSample(
            id="s1",
            title="Sample 1",
            content=sample_text,
            analysis=analysis,
        )
    ]
    prompt_context = VoiceCalibrator.build_voice_context(samples)
    assert "conversational" in prompt_context.lower()
    assert "contractions" in prompt_context.lower()
