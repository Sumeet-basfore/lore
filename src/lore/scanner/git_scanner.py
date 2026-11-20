"""Git repository history scanner and diff statistics analyzer."""

import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from lore.core.exceptions import ScannerError
from lore.core.models import GitCommit
from lore.scanner.filters import is_noise_commit, is_noise_file, is_secret_file


class GitScanner:
    """Scans git history, extracting structured commits, diff metrics, and release tags."""

    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path).resolve()
        # Support worktrees, submodules (.git file) and normal git repos (.git dir)
        if not (self.repo_path / ".git").exists():
            raise ScannerError(f"Directory is not a git repository: {self.repo_path}")

    def _run_git(self, args: List[str]) -> str:
        """Executes a git command inside the repository directory."""
        try:
            res = subprocess.run(
                ["git", *args],
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                check=True,
            )
            return res.stdout
        except subprocess.CalledProcessError as e:
            # Handle empty repository gracefully
            if "does not have any commits yet" in e.stderr or "unknown revision or path" in e.stderr:
                return ""
            raise ScannerError(f"Git command failed ('git {' '.join(args)}'): {e.stderr.strip()}") from e

    def get_current_branch(self) -> str:
        """Returns the active branch name or 'HEAD'."""
        try:
            branch = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"]).strip()
            return branch if branch else "HEAD"
        except Exception:
            return "HEAD"

    def get_diff_text(self, commit_sha: str) -> str:
        """Retrieves patch diff for a given commit."""
        try:
            return self._run_git(["show", "--format=", commit_sha])
        except Exception:
            return ""

    def scan_commits(
        self,
        since: Optional[str] = None,
        until: Optional[str] = None,
        max_commits: int = 200,
        exclude_patterns: Optional[List[str]] = None,
        include_wip: bool = False,
    ) -> List[GitCommit]:
        """Extracts structured commit history with file metrics, excluding secrets and noise."""
        # Use ASCII unit separators: 0x1f between fields, 0x1e between commits
        delimiter_field = "%x1f"
        delimiter_record = "%x1e"
        format_str = f"{delimiter_record}%H{delimiter_field}%h{delimiter_field}%an{delimiter_field}%ae{delimiter_field}%aI{delimiter_field}%s{delimiter_field}%b"

        cmd = ["log", f"--format={format_str}", "--numstat", f"-n{max_commits}"]
        if since:
            cmd.append(f"--since={since}")
        if until:
            cmd.append(f"--until={until}")

        raw_output = self._run_git(cmd)
        if not raw_output.strip():
            return []

        commits: List[GitCommit] = []
        raw_chunks = raw_output.split("\x1e")

        for chunk in raw_chunks:
            chunk = chunk.strip()
            if not chunk:
                continue

            parts = chunk.split("\x1f")
            if len(parts) < 7:
                continue

            sha = parts[0].strip()
            short_sha = parts[1].strip()
            author = parts[2].strip()
            email = parts[3].strip()
            date_str = parts[4].strip()
            subject = parts[5].strip()
            rest = parts[6]

            # The rest contains the body and the numstat lines
            body_lines = []
            files_changed = []
            total_insertions = 0
            total_deletions = 0

            for line in rest.splitlines():
                line = line.strip()
                if not line:
                    continue
                match = re.match(r"^(\d+|-)\s+(\d+|-)\s+(.+)$", line)
                if match:
                    ins_str, del_str, file_path = match.groups()
                    if is_secret_file(file_path):
                        continue
                    if not is_noise_file(file_path):
                        ins = int(ins_str) if ins_str.isdigit() else 0
                        dels = int(del_str) if del_str.isdigit() else 0
                        total_insertions += ins
                        total_deletions += dels
                        files_changed.append(file_path)
                else:
                    body_lines.append(line)

            full_message = f"{subject}\n\n{chr(10).join(body_lines)}".strip()

            is_noise = is_noise_commit(subject, exclude_patterns)
            if is_noise and not include_wip:
                continue

            try:
                commit_dt = datetime.fromisoformat(date_str)
            except Exception:
                commit_dt = datetime.now(timezone.utc)

            commits.append(
                GitCommit(
                    sha=sha,
                    short_sha=short_sha,
                    author=author,
                    email=email,
                    timestamp=commit_dt,
                    message=full_message,
                    summary=subject,
                    files_changed=files_changed,
                    insertions=total_insertions,
                    deletions=total_deletions,
                    is_low_entropy=bool(is_noise),
                )
            )

        return commits

    def scan_working_tree(self) -> Optional[GitCommit]:
        """Inspects uncommitted changes in working tree and staged index."""
        try:
            status_output = self._run_git(["status", "--porcelain"])
            if not status_output.strip():
                return None

            diff_stat = self._run_git(["diff", "HEAD", "--numstat"])
            files_changed = []
            total_ins = 0
            total_del = 0

            for line in diff_stat.splitlines():
                m = re.match(r"^(\d+|-)\s+(\d+|-)\s+(.+)$", line.strip())
                if m:
                    ins_str, del_str, file_path = m.groups()
                    if not is_secret_file(file_path) and not is_noise_file(file_path):
                        files_changed.append(file_path)
                        if ins_str.isdigit():
                            total_ins += int(ins_str)
                        if del_str.isdigit():
                            total_del += int(del_str)

            if not files_changed:
                return None

            return GitCommit(
                sha="0000000000000000000000000000000000000000",
                short_sha="working",
                author="Working Tree",
                email="local@dev",
                timestamp=datetime.now(timezone.utc),
                message="Uncommitted working tree changes",
                summary="Working tree uncommitted changes",
                files_changed=files_changed,
                insertions=total_ins,
                deletions=total_del,
                is_low_entropy=False,
            )
        except Exception:
            return None

    def get_tags(self) -> List[Dict[str, str]]:
        """Returns release tags with commit hashes."""
        try:
            output = self._run_git(["tag", "-l", "--sort=-creatordate", "--format=%(refname:short)%09%(objectname:short)%09%(creatordate:iso)"])
            tags = []
            for line in output.splitlines():
                parts = line.strip().split("\t")
                if len(parts) >= 2:
                    tags.append({
                        "name": parts[0],
                        "sha": parts[1],
                        "date": parts[2] if len(parts) > 2 else "",
                    })
            return tags
        except Exception:
            return []

    def get_summary_stats(self, since: Optional[str] = None) -> Dict[str, Any]:
        """Computes aggregate stats over the scanned period."""
        commits = self.scan_commits(since=since)
        unique_files = set()
        total_insertions = 0
        total_deletions = 0

        for c in commits:
            unique_files.update(c.files_changed)
            total_insertions += c.insertions
            total_deletions += c.deletions

        return {
            "total_commits": len(commits),
            "files_modified_count": len(unique_files),
            "total_insertions": total_insertions,
            "total_deletions": total_deletions,
            "unique_files": sorted(list(unique_files)),
        }
