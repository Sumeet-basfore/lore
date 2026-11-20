"""Custom domain exceptions for Lore."""


class LoreError(Exception):
    """Base exception for all Lore errors."""
    pass


class ConfigError(LoreError):
    """Raised when configuration is missing or invalid."""
    pass


class DatabaseError(LoreError):
    """Raised on SQLite database errors."""
    pass


class ScannerError(LoreError):
    """Raised during git or project scanning."""
    pass


class ExtractionError(LoreError):
    """Raised during content atom extraction."""
    pass


class LLMRouteError(LoreError):
    """Raised during LLM prompt execution or routing."""
    pass


class HumanizerError(LoreError):
    """Raised during anti-slop humanization passes."""
    pass
