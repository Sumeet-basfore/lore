"""Evidence ledger builder and verification utilities."""

from typing import List, Optional
from lore.core.models import EvidenceRecord, GitCommit


def build_evidence_from_commits(commits: List[GitCommit]) -> EvidenceRecord:
    """Constructs an immutable EvidenceRecord from a group of related commits."""
    if not commits:
        return EvidenceRecord()

    shas = [c.sha for c in commits]
    unique_files = set()
    total_insertions = 0
    total_deletions = 0
    sample_messages = []

    for c in commits:
        unique_files.update(c.files_changed)
        total_insertions += c.insertions
        total_deletions += c.deletions
        sample_messages.append(c.summary)

    # Sort commits by timestamp
    sorted_commits = sorted(commits, key=lambda x: x.timestamp)
    date_start = sorted_commits[0].timestamp
    date_end = sorted_commits[-1].timestamp

    # Select the most frequently modified or representative files
    key_files = sorted(list(unique_files))[:8]

    return EvidenceRecord(
        commits=shas,
        files_changed=len(unique_files),
        insertions=total_insertions,
        deletions=total_deletions,
        date_start=date_start,
        date_end=date_end,
        key_files=key_files,
        sample_messages=sample_messages[:5],
    )
