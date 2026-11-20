"""Filtering logic for secrets, noise commits, and machine artifacts."""

import re
from pathlib import Path
from typing import List, Optional

# Secret patterns that must NEVER be inspected, shown, or used in content
SECRET_FILE_PATTERNS = [
    r"^\.env(\..+)?$",
    r".*\.pem$",
    r".*\.key$",
    r".*\.pkcs12$",
    r".*\.pfx$",
    r"id_rsa.*",
    r"id_ed25519.*",
    r".*secret.*",
    r".*credential.*",
    r".*token\.json$",
    r"service-account.*\.json$",
    r".*private.*key.*",
]

# Files that produce high diff noise without conveying developer intent
NOISE_FILE_PATTERNS = [
    r".*package-lock\.json$",
    r".*yarn\.lock$",
    r".*pnpm-lock\.yaml$",
    r".*Cargo\.lock$",
    r".*poetry\.lock$",
    r".*uv\.lock$",
    r".*\.min\.js$",
    r".*\.min\.css$",
    r".*\.map$",
    r".*\.tsbuildinfo$",
    r".*\.pyc$",
    r".*__pycache__.*",
    r".*\.DS_Store$",
]

DEFAULT_NOISE_COMMIT_PREFIXES = [
    "merge branch",
    "merge pull request",
    "merge remote-tracking branch",
    "fix typo",
    "typo",
    "wip",
    "work in progress",
    "checkpoint",
    "formatting",
    "format code",
]


def is_secret_file(file_path: str) -> bool:
    """Returns True if the file matches known credential or secret patterns."""
    basename = Path(file_path).name.lower()
    for pattern in SECRET_FILE_PATTERNS:
        if re.search(pattern, basename, re.IGNORECASE):
            return True
    return False


def is_noise_file(file_path: str) -> bool:
    """Returns True if the file is a lockfile, minified file, or build artifact."""
    norm_path = file_path.replace("\\", "/").lower()
    for pattern in NOISE_FILE_PATTERNS:
        if re.search(pattern, norm_path, re.IGNORECASE):
            return True
    return False


def is_noise_commit(message: str, custom_exclude_patterns: Optional[List[str]] = None) -> bool:
    """Determines whether a commit message represents automated noise or trivial work."""
    clean_msg = message.strip().lower()
    if not clean_msg:
        return True

    patterns = list(DEFAULT_NOISE_COMMIT_PREFIXES)
    if custom_exclude_patterns:
        patterns.extend([p.lower() for p in custom_exclude_patterns])

    for prefix in patterns:
        if clean_msg.startswith(prefix):
            return True
        if f": {prefix}" in clean_msg:
            return True

    return False
