"""Narrative angle generator and 7-angle story framing engine."""

from typing import Any, Dict, List, Optional
from lore.core.models import AtomType, ContentAtom, Platform


class StoryAngle:
    def __init__(
        self,
        name: str,
        hook: str,
        narrative_arc: str,
        best_platforms: List[Platform],
        rationale: str,
    ):
        self.name = name
        self.hook = hook
        self.narrative_arc = narrative_arc
        self.best_platforms = best_platforms
        self.rationale = rationale

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "hook": self.hook,
            "narrative_arc": self.narrative_arc,
            "best_platforms": [p.value for p in self.best_platforms],
            "rationale": self.rationale,
        }


class AngleFinder:
    """Discovers high-engagement narrative angles for a given Content Atom across 7 technical angles."""

    # 7 Canonical Developer Angles
    ARCHITECTURE_TRADEOFF = "ARCHITECTURE_TRADEOFF"
    POST_MORTEM_BUG = "POST_MORTEM_BUG"
    BEFORE_AFTER_BENCHMARK = "BEFORE_AFTER_BENCHMARK"
    FEATURE_DROP = "FEATURE_DROP"
    WHAT_WE_DELETED = "WHAT_WE_DELETED"
    TIL_LANGUAGE_QUIRK = "TIL_LANGUAGE_QUIRK"
    PROTOTYPE_HACK = "PROTOTYPE_HACK"

    @classmethod
    def find_angles(cls, atom: ContentAtom) -> List[StoryAngle]:
        angles: List[StoryAngle] = []
        ev = atom.evidence
        title = atom.title
        tech = ", ".join(atom.tech_stack[:3]) if atom.tech_stack else "our stack"

        if atom.atom_type == AtomType.FEATURE:
            # Angle 1: Direct Problem -> Solution
            angles.append(
                StoryAngle(
                    name="Problem-Solution",
                    hook=f"We just shipped {title} to eliminate manual overhead.",
                    narrative_arc="The friction we faced -> The decision to build it -> How it works -> The result",
                    best_platforms=[Platform.TWITTER, Platform.LINKEDIN],
                    rationale="Direct, clear, demonstrates tangible momentum.",
                )
            )
            # Angle 2: Technical Deep Dive
            angles.append(
                StoryAngle(
                    name="Technical Deep Dive",
                    hook=f"How we built {title} in {tech} across {ev.files_changed} files without external bloat.",
                    narrative_arc="Architecture constraints -> Technical trade-offs -> Implementation details -> Lessons",
                    best_platforms=[Platform.THREAD, Platform.BLOG],
                    rationale="High signal for engineers interested in implementation specifics.",
                )
            )
            # Angle 3: Contrarian / Trade-off
            angles.append(
                StoryAngle(
                    name="The Trade-off",
                    hook=f"Why we built {title} in-house instead of adopting another third-party library.",
                    narrative_arc="The conventional wisdom -> Why it failed our scale -> The custom solution -> Benchmarks",
                    best_platforms=[Platform.TWITTER, Platform.LINKEDIN],
                    rationale="Sparks healthy discussion and showcases engineering maturity.",
                )
            )
            # 7-Angle Feature Drop
            angles.append(
                StoryAngle(
                    name=cls.FEATURE_DROP,
                    hook=f"Shipped {title} in {tech} with zero external dependencies.",
                    narrative_arc="The user friction -> The design pattern -> The implementation -> Try it out",
                    best_platforms=[Platform.TWITTER, Platform.LINKEDIN, Platform.CHANGELOG],
                    rationale="Direct, clear, demonstrates tangible momentum.",
                )
            )

        elif atom.atom_type == AtomType.BUGFIX:
            # Angle 1: The War Story
            angles.append(
                StoryAngle(
                    name="The War Story",
                    hook=f"A subtle bug was slowing down {title.lower()}. Here's what was actually happening.",
                    narrative_arc="The symptom in production -> The red herring we chased -> The root cause in diff -> The fix",
                    best_platforms=[Platform.TWITTER, Platform.THREAD, Platform.LINKEDIN],
                    rationale="Developers love relatable debugging mysteries with concrete root causes.",
                )
            )
            # Angle 2: Defensive Engineering Lesson
            angles.append(
                StoryAngle(
                    name="Engineering Lesson",
                    hook=f"The test case we should have written before shipping {title.lower()}.",
                    narrative_arc="The assumption we made -> What broke -> The regression test added -> The takeaway",
                    best_platforms=[Platform.BLOG, Platform.THREAD],
                    rationale="Educational and builds trust through vulnerability and technical honesty.",
                )
            )
            # 7-Angle Post Mortem
            angles.append(
                StoryAngle(
                    name=cls.POST_MORTEM_BUG,
                    hook=f"A subtle race condition broke {title.lower()} under load. Here's what actually happened.",
                    narrative_arc="The symptom in production -> The red herring we chased -> The root cause in diff -> The fix",
                    best_platforms=[Platform.TWITTER, Platform.THREAD, Platform.LINKEDIN],
                    rationale="Detailed post-mortem breakdown.",
                )
            )

        elif atom.atom_type == AtomType.REFACTOR:
            angles.append(
                StoryAngle(
                    name="Clean Architecture",
                    hook=f"We deleted lines of code and simplified {title.lower()}.",
                    narrative_arc="The technical debt we accumulated -> The breaking point -> The refactor strategy -> The cleaner codebase",
                    best_platforms=[Platform.LINKEDIN, Platform.BLOG, Platform.TWITTER],
                    rationale="Engineers celebrate deleting code and reducing complexity.",
                )
            )
            angles.append(
                StoryAngle(
                    name=cls.WHAT_WE_DELETED,
                    hook=f"Deleted {ev.deletions} lines of unnecessary abstractions in {title.lower()}.",
                    narrative_arc="The technical debt we accumulated -> The breaking point -> What we cut -> The simpler system",
                    best_platforms=[Platform.TWITTER, Platform.LINKEDIN, Platform.BLOG],
                    rationale="Engineers celebrate deleting code and reducing cognitive complexity.",
                )
            )

        elif atom.atom_type == AtomType.MILESTONE:
            angles.append(
                StoryAngle(
                    name="Release Milestone",
                    hook=f"Shipped {title}. Here is everything included and what is next.",
                    narrative_arc="The milestone reached -> Key capabilities unlocked -> Next roadmap focus",
                    best_platforms=[Platform.CHANGELOG, Platform.TWITTER, Platform.LINKEDIN],
                    rationale="Celebrates progress and keeps users informed of updates.",
                )
            )

        # Always add Architecture Tradeoff, Benchmark, TIL, and Prototype Hack
        angles.append(
            StoryAngle(
                name=cls.ARCHITECTURE_TRADEOFF,
                hook=f"Why we chose {tech} for {title} instead of the conventional alternative.",
                narrative_arc="The architectural constraint -> Trade-offs evaluated -> Why the standard path failed -> The decision",
                best_platforms=[Platform.TWITTER, Platform.LINKEDIN, Platform.BLOG],
                rationale="Sparks healthy technical debate and showcases engineering maturity.",
            )
        )

        if ev.insertions > 0 or ev.deletions > 0:
            angles.append(
                StoryAngle(
                    name=cls.BEFORE_AFTER_BENCHMARK,
                    hook=f"Benchmarking {title.lower()}: cutting overhead across {ev.files_changed} files.",
                    narrative_arc="The baseline benchmark -> Profiling the bottleneck -> The targeted code diff -> Measured result",
                    best_platforms=[Platform.TWITTER, Platform.LINKEDIN, Platform.BLOG],
                    rationale="Concrete numbers and benchmark comparisons build immediate credibility.",
                )
            )

        angles.append(
            StoryAngle(
                name=cls.TIL_LANGUAGE_QUIRK,
                hook=f"A {tech} standard library nuance we ran into while implementing {title.lower()}.",
                narrative_arc="The unexpected behavior -> The compiler/runtime detail -> The idiomatic pattern",
                best_platforms=[Platform.TWITTER, Platform.THREAD],
                rationale="Educational micro-lessons perform exceptionally well on technical Twitter.",
            )
        )

        angles.append(
            StoryAngle(
                name=cls.PROTOTYPE_HACK,
                hook=f"Prototyping {title.lower()} in under 100 lines of code before rewriting it.",
                narrative_arc="The scratchpad experiment -> What worked vs failed -> Porting to production",
                best_platforms=[Platform.TWITTER, Platform.THREAD, Platform.LINKEDIN],
                rationale="Highlights rapid iteration and scrappy builder mindset.",
            )
        )

        return angles
