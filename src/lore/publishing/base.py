"""Base models and types for publishing subsystem."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, model_validator


class PublishOutcome(str, Enum):
    """Distinguishes a completed post from a hand-off or local simulation."""

    PUBLISHED = "published"
    HANDOFF = "handoff"
    SIMULATED = "simulated"
    FAILED = "failed"


class PublishResult(BaseModel):
    """Result of a publish attempt; only provider-confirmed posts are published."""

    success: bool
    outcome: PublishOutcome
    platform: str
    published_url: Optional[str] = None
    action_url: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
    retryable: bool = False
    retry_after_seconds: Optional[int] = None

    @model_validator(mode="after")
    def validate_outcome(self) -> "PublishResult":
        if self.success != (self.outcome != PublishOutcome.FAILED):
            raise ValueError("success must agree with the publication outcome")
        if self.outcome != PublishOutcome.PUBLISHED and self.published_url is not None:
            raise ValueError("published_url is only valid for a provider-confirmed publication")
        if self.outcome == PublishOutcome.HANDOFF and self.action_url is None:
            raise ValueError("handoff outcomes require an action_url")
        return self
