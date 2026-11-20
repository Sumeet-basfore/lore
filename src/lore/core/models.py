"""Core Pydantic data models for Lore."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AtomType(str, Enum):
    FEATURE = "feature"
    BUGFIX = "bugfix"
    REFACTOR = "refactor"
    MILESTONE = "milestone"
    STACK_DECISION = "stack_decision"


class Platform(str, Enum):
    TWITTER = "twitter"
    THREAD = "thread"
    LINKEDIN = "linkedin"
    BLOG = "blog"
    CHANGELOG = "changelog"
    BLUESKY = "bluesky"
    GITHUB = "github"


class DraftStatus(str, Enum):
    DRAFTED = "drafted"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"


class GitCommit(BaseModel):
    """Represents an individual git commit."""
    sha: str
    short_sha: str
    author: str
    email: str
    timestamp: datetime
    message: str
    summary: str
    files_changed: List[str] = Field(default_factory=list)
    insertions: int = 0
    deletions: int = 0
    is_low_entropy: bool = False


class Project(BaseModel):
    """A registered repository or project directory."""
    id: str
    name: str
    path: str
    description: Optional[str] = None
    tech_stack: List[str] = Field(default_factory=list)
    last_scanned_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utc_now)


class EvidenceRecord(BaseModel):
    """Immutable evidence backing a Content Atom."""
    commits: List[str] = Field(default_factory=list)  # list of commit SHAs
    files_changed: int = 0
    insertions: int = 0
    deletions: int = 0
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None
    key_files: List[str] = Field(default_factory=list)
    sample_messages: List[str] = Field(default_factory=list)


class ContentAtom(BaseModel):
    """An extracted, atomic engineering accomplishment."""
    id: str
    project_id: str
    atom_type: AtomType
    title: str
    summary: str
    evidence: EvidenceRecord
    tech_stack: List[str] = Field(default_factory=list)
    potential_score: float = 0.5  # 0.0 to 1.0
    status: str = "unprocessed"  # unprocessed, drafted, archived
    created_at: datetime = Field(default_factory=utc_now)


class Draft(BaseModel):
    """A generated content draft for a specific platform."""
    id: str
    atom_id: Optional[str] = None
    project_id: str
    platform: Platform
    title: Optional[str] = None
    raw_content: str
    humanized_content: str
    humanizer_audit: Dict[str, Any] = Field(default_factory=dict)
    status: DraftStatus = DraftStatus.DRAFTED
    published_url: Optional[str] = None
    published_at: Optional[datetime] = None
    card_image_path: Optional[str] = None
    dlp_status: str = "clean"
    dlp_audit_json: Optional[Dict[str, Any]] = None
    scheduled_for: Optional[datetime] = None
    channel_target: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class VoiceSample(BaseModel):
    """A writing sample used to calibrate the author's voice."""
    id: str
    title: str
    content: str
    analysis: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class LoreConfig(BaseModel):
    """Global configuration settings."""
    version: str = "1"
    llm_provider: str = "ollama"  # ollama | openai | anthropic | openrouter | gemini
    llm_model: str = "gemma4:e2b"
    ollama_base_url: str = "http://localhost:11434"
    api_key: Optional[str] = None
    author_name: str = "Developer"
    author_handle: str = "@builder"
    default_platforms: List[Platform] = Field(
        default_factory=lambda: [Platform.TWITTER, Platform.LINKEDIN, Platform.BLOG]
    )
    exclude_patterns: List[str] = Field(
        default_factory=lambda: [
            "merge branch",
            "fix typo",
            "wip",
            "chore:",
            "style:",
            "bump version",
        ]
    )


class DLPAuditLog(BaseModel):
    """Compliance audit log entry for scanned assets."""
    id: str
    target_type: str  # 'commit', 'atom', 'draft'
    target_id: str
    draft_id: Optional[str] = None
    scanned_at: datetime = Field(default_factory=utc_now)
    rules_evaluated: int = 0
    violations_detected: int = 0
    masked_entities_json: Optional[Dict[str, Any]] = None
    highest_entropy_score: float = 0.0
    status: str = "PASSED"  # 'PASSED', 'REDACTED', 'BLOCKED'


class PublishQueueItem(BaseModel):
    """Scheduled publication queue item."""
    id: str
    draft_id: str
    platform: Platform
    scheduled_time: datetime
    attempts: int = 0
    last_error: Optional[str] = None
    status: str = "pending"  # 'pending', 'publishing', 'success', 'failed'
    created_at: datetime = Field(default_factory=utc_now)


class ASTDiffReport(BaseModel):
    """Structural AST diff analysis report."""
    hero_file: Optional[str] = None
    modified_classes: List[str] = Field(default_factory=list)
    modified_functions: List[str] = Field(default_factory=list)
    schema_migrations: List[str] = Field(default_factory=list)
    inline_comments: List[str] = Field(default_factory=list)
    test_assertions: List[str] = Field(default_factory=list)
    synthesized_summary: Optional[str] = None
