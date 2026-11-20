"""Base models and types for publishing subsystem."""

from typing import Optional
from pydantic import BaseModel


class PublishResult(BaseModel):
    """Result of a social media publishing operation."""
    success: bool
    platform: str
    published_url: Optional[str] = None
    error: Optional[str] = None
    retry_after_seconds: Optional[int] = None
