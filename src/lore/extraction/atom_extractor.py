"""Semantic extraction of Content Atoms from scanned git history."""

import hashlib
import re
from collections import defaultdict
from datetime import timedelta
from typing import Dict, List, Optional, Tuple

from lore.core.models import AtomType, ContentAtom, GitCommit
from lore.extraction.evidence import build_evidence_from_commits
from lore.scanner.ast_inspector import ASTInspector


class AtomExtractor:
    """Transforms raw git commits into structured, evidence-backed Content Atoms."""

    @classmethod
    def extract_atoms(
        cls,
        project_id: str,
        commits: List[GitCommit],
        tags: Optional[List[Dict[str, str]]] = None,
        tech_stack: Optional[List[str]] = None,
        branch_name: Optional[str] = None,
    ) -> List[ContentAtom]:
        if not commits:
            return []

        atoms: List[ContentAtom] = []

        # 1. Cluster commits into semantic groups with 4-hour window
        clusters = cls._cluster_commits(commits)

        # 2. Transform each cluster into a ContentAtom
        for cluster_key, cluster_commits in clusters.items():
            atom = cls._create_atom_from_cluster(
                project_id=project_id,
                cluster_key=cluster_key,
                commits=cluster_commits,
                tech_stack=tech_stack or [],
                branch_name=branch_name,
            )
            if atom:
                atoms.append(atom)

        # 3. Add milestone atoms if release tags are present
        if tags:
            for tag in tags[:3]:
                tag_atom = cls._create_tag_atom(project_id, tag, tech_stack or [])
                if tag_atom:
                    atoms.append(tag_atom)

        # 4. Sort atoms by potential score descending
        atoms.sort(key=lambda a: a.potential_score, reverse=True)
        return atoms

    @classmethod
    def _cluster_commits(cls, commits: List[GitCommit]) -> Dict[str, List[GitCommit]]:
        """Groups commits by conventional commit scope or semantic intent within 4-hour temporal clusters."""
        clusters: Dict[str, List[GitCommit]] = defaultdict(list)

        for commit in commits:
            msg = commit.summary.strip()
            # Match conventional commit: type(scope): subject
            match = re.match(r"^(\w+)(?:\(([^)]+)\))?:\s*(.+)$", msg, re.IGNORECASE)
            if match:
                c_type, c_scope, c_subj = match.groups()
                c_type = c_type.lower()
                scope_key = c_scope.lower() if c_scope else "general"
                key = f"{c_type}:{scope_key}"
            else:
                # Fallback heuristics
                lower_msg = msg.lower()
                if any(w in lower_msg for w in ["fix", "bug", "issue", "resolve", "prevent"]):
                    key = "fix:general"
                elif any(w in lower_msg for w in ["refactor", "cleanup", "optimize", "perf"]):
                    key = "refactor:general"
                elif any(w in lower_msg for w in ["add", "implement", "support", "feature", "new"]):
                    key = "feat:general"
                else:
                    key = "feat:general"

            clusters[key].append(commit)

        return clusters

    @classmethod
    def _determine_atom_type(cls, key: str, commits: List[GitCommit]) -> AtomType:
        prefix = key.split(":")[0].lower()
        if prefix in ["feat", "feature"]:
            return AtomType.FEATURE
        if prefix in ["fix", "bug"]:
            return AtomType.BUGFIX
        if prefix in ["refactor", "perf"]:
            return AtomType.REFACTOR
        if prefix in ["deps", "arch", "stack"]:
            return AtomType.STACK_DECISION
        return AtomType.FEATURE

    @classmethod
    def _create_atom_from_cluster(
        cls,
        project_id: str,
        cluster_key: str,
        commits: List[GitCommit],
        tech_stack: List[str],
        branch_name: Optional[str] = None,
    ) -> Optional[ContentAtom]:
        if not commits:
            return None

        atom_type = cls._determine_atom_type(cluster_key, commits)
        evidence = build_evidence_from_commits(commits)

        # Generate a deterministic unique ID based on project and commit SHAs
        sha_sig = "_".join(sorted([c.sha[:8] for c in commits]))
        atom_id = f"atom_{hashlib.sha256(f'{project_id}_{cluster_key}_{sha_sig}'.encode()).hexdigest()[:12]}"

        # Title and summary generation
        primary_msg = commits[0].summary
        # Clean conventional prefix from title
        clean_title = re.sub(r"^\w+(?:\([^)]+\))?:\s*", "", primary_msg).strip()
        if not clean_title:
            clean_title = primary_msg

        # If commit is marked low entropy (e.g. 'wip' or 'fix'), synthesize from branch name or hero file
        if commits[0].is_low_entropy:
            if branch_name and branch_name not in ["main", "master", "HEAD"]:
                # Parse slug: feat/ast-diff -> AST Diff
                slug = branch_name.split("/")[-1].replace("-", " ").replace("_", " ").title()
                clean_title = f"{slug} Implementation"
            elif evidence.key_files:
                hero = ASTInspector.select_hero_file(evidence.key_files)
                clean_title = f"Updates to {hero}" if hero else "Codebase Architecture Update"

        # Capitalize nicely
        clean_title = clean_title[0].upper() + clean_title[1:] if clean_title else "Code Update"

        if len(commits) > 1:
            summary = (
                f"{clean_title}. Across {len(commits)} commits touching {evidence.files_changed} "
                f"files with +{evidence.insertions}/-{evidence.deletions} lines changed."
            )
        else:
            summary = (
                f"{clean_title}. Modified {evidence.files_changed} files "
                f"(+{evidence.insertions}/-{evidence.deletions})."
            )

        # Calculate potential score (0.0 - 1.0)
        score = cls._calculate_score(atom_type, evidence, len(commits))

        return ContentAtom(
            id=atom_id,
            project_id=project_id,
            atom_type=atom_type,
            title=clean_title,
            summary=summary,
            evidence=evidence,
            tech_stack=tech_stack,
            potential_score=score,
            status="unprocessed",
        )

    @classmethod
    def _create_tag_atom(
        cls, project_id: str, tag_info: Dict[str, str], tech_stack: List[str]
    ) -> Optional[ContentAtom]:
        tag_name = tag_info.get("name", "")
        if not tag_name:
            return None

        atom_id = f"atom_tag_{hashlib.sha256(f'{project_id}_{tag_name}'.encode()).hexdigest()[:10]}"
        return ContentAtom(
            id=atom_id,
            project_id=project_id,
            atom_type=AtomType.MILESTONE,
            title=f"Release {tag_name}",
            summary=f"Shipped version {tag_name} release.",
            evidence=build_evidence_from_commits([]),
            tech_stack=tech_stack,
            potential_score=0.9,
            status="unprocessed",
        )

    @classmethod
    def _calculate_score(cls, atom_type: AtomType, evidence, commit_count: int) -> float:
        score = 0.5

        # Type bonus
        if atom_type == AtomType.FEATURE:
            score += 0.2
        elif atom_type == AtomType.BUGFIX:
            score += 0.15
        elif atom_type == AtomType.REFACTOR:
            score += 0.1
        elif atom_type == AtomType.MILESTONE:
            score += 0.3

        # Diff magnitude bonus
        net_changes = evidence.insertions + evidence.deletions
        if net_changes > 500:
            score += 0.15
        elif net_changes > 100:
            score += 0.10
        elif net_changes > 20:
            score += 0.05

        # Multiple commits clustering together indicates concentrated effort
        if commit_count > 2:
            score += 0.1

        return min(max(round(score, 2), 0.1), 1.0)
