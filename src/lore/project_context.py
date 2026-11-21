"""Git repository discovery used by the CLI's current-project defaults."""

import subprocess
from pathlib import Path
from typing import Optional


def find_git_root(cwd: Optional[Path] = None) -> Optional[Path]:
    """Return the current Git worktree root, or ``None`` outside a repository."""
    working_directory = (cwd or Path.cwd()).expanduser().resolve()
    try:
        result = subprocess.run(
            ["git", "-C", str(working_directory), "rev-parse", "--show-toplevel"],
            capture_output=True,
            check=False,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError, RuntimeError):
        return None

    if result.returncode != 0 or not result.stdout.strip():
        return None

    try:
        return Path(result.stdout.strip()).expanduser().resolve()
    except (OSError, RuntimeError):
        return None
