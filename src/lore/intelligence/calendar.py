"""Content Calendar and posting schedule planner."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from lore.core.models import ContentAtom, Platform
from lore.intelligence.angle_finder import AngleFinder


class CalendarSlot:
    """Represents a scheduled content opportunity."""

    def __init__(
        self,
        date: datetime,
        day_of_week: str,
        atom: ContentAtom,
        platform: Platform,
        angle_name: str,
        suggested_hook: str,
    ):
        self.date = date
        self.day_of_week = day_of_week
        self.atom = atom
        self.platform = platform
        self.angle_name = angle_name
        self.suggested_hook = suggested_hook

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date.strftime("%Y-%m-%d"),
            "day_of_week": self.day_of_week,
            "project_id": self.atom.project_id,
            "atom_title": self.atom.title,
            "atom_type": self.atom.atom_type.value,
            "platform": self.platform.value,
            "angle": self.angle_name,
            "suggested_hook": self.suggested_hook,
        }


class ContentCalendar:
    """Generates an optimized content schedule from extracted atoms."""

    @classmethod
    def plan_week(
        cls, atoms: List[ContentAtom], start_date: Optional[datetime] = None
    ) -> List[CalendarSlot]:
        if not atoms:
            return []

        start = start_date or datetime.now(timezone.utc)
        schedule: List[CalendarSlot] = []

        # Sort atoms by score descending
        sorted_atoms = sorted(atoms, key=lambda a: a.potential_score, reverse=True)

        # Platform cadence pattern across 5 workdays
        day_cadence = [
            (0, Platform.LINKEDIN),  # Monday: Thought leadership / architecture
            (1, Platform.TWITTER),   # Tuesday: Punchy feature ship
            (2, Platform.THREAD),    # Wednesday: In-depth thread / walkthrough
            (3, Platform.LINKEDIN),  # Thursday: Engineering lesson / story
            (4, Platform.TWITTER),   # Friday: Milestone / week in review
        ]

        atom_idx = 0
        total_atoms = len(sorted_atoms)

        for day_offset, platform in day_cadence:
            slot_date = start + timedelta(days=day_offset)
            atom = sorted_atoms[atom_idx % total_atoms]
            atom_idx += 1

            angles = AngleFinder.find_angles(atom)
            # Find best angle matching this platform, or first
            matching_angle = next(
                (a for a in angles if platform in a.best_platforms), angles[0]
            )

            schedule.append(
                CalendarSlot(
                    date=slot_date,
                    day_of_week=slot_date.strftime("%A"),
                    atom=atom,
                    platform=platform,
                    angle_name=matching_angle.name,
                    suggested_hook=matching_angle.hook,
                )
            )

        return schedule
