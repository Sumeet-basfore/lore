"""SQLite database storage layer for Lore."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from lore.config import get_lore_home
from lore.core.exceptions import DatabaseError
from lore.core.models import (
    AtomType,
    ContentAtom,
    Draft,
    DraftStatus,
    EvidenceRecord,
    Platform,
    Project,
    VoiceSample,
)


class Database:
    """Manages SQLite persistence for projects, content atoms, drafts, and voice samples."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            self.db_path = get_lore_home() / "lore.db"
        else:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self) -> None:
        """Initializes tables and indexes."""
        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    path TEXT NOT NULL UNIQUE,
                    description TEXT,
                    tech_stack TEXT, -- JSON array
                    last_scanned_at TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS content_atoms (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    atom_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    evidence TEXT NOT NULL, -- JSON object
                    tech_stack TEXT, -- JSON array
                    potential_score REAL DEFAULT 0.5,
                    status TEXT DEFAULT 'unprocessed',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS drafts (
                    id TEXT PRIMARY KEY,
                    atom_id TEXT,
                    project_id TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    title TEXT,
                    raw_content TEXT NOT NULL,
                    humanized_content TEXT NOT NULL,
                    humanizer_audit TEXT, -- JSON object
                    status TEXT DEFAULT 'drafted',
                    published_url TEXT,
                    published_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (atom_id) REFERENCES content_atoms(id) ON DELETE SET NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS voice_samples (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    analysis TEXT, -- JSON object
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_atoms_project ON content_atoms(project_id);
                CREATE INDEX IF NOT EXISTS idx_atoms_status ON content_atoms(status);
                CREATE INDEX IF NOT EXISTS idx_drafts_project ON drafts(project_id);
                CREATE INDEX IF NOT EXISTS idx_drafts_status ON drafts(status);
                CREATE INDEX IF NOT EXISTS idx_drafts_platform ON drafts(platform);
                """
            )

    # ---------------------------------------------------------
    # Project Operations
    # ---------------------------------------------------------

    def add_project(self, project: Project) -> None:
        with self._get_connection() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO projects (id, name, path, description, tech_stack, last_scanned_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        project.id,
                        project.name,
                        project.path,
                        project.description,
                        json.dumps(project.tech_stack),
                        project.last_scanned_at.isoformat() if project.last_scanned_at else None,
                        project.created_at.isoformat(),
                    ),
                )
            except sqlite3.IntegrityError as e:
                raise DatabaseError(f"Project name or path already registered: {e}") from e

    def get_project(self, id_or_name: str) -> Optional[Project]:
        with self._get_connection() as conn:
            cur = conn.execute(
                "SELECT * FROM projects WHERE id = ? OR name = ?", (id_or_name, id_or_name)
            )
            row = cur.fetchone()
            if not row:
                return None
            return self._row_to_project(row)

    def list_projects(self) -> List[Project]:
        with self._get_connection() as conn:
            cur = conn.execute("SELECT * FROM projects ORDER BY name ASC")
            return [self._row_to_project(r) for r in cur.fetchall()]

    def update_project_scan_time(self, project_id: str, scanned_at: datetime) -> None:
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE projects SET last_scanned_at = ? WHERE id = ?",
                (scanned_at.isoformat(), project_id),
            )

    def update_project_tech_stack(self, project_id: str, tech_stack: List[str]) -> None:
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE projects SET tech_stack = ? WHERE id = ?",
                (json.dumps(tech_stack), project_id),
            )

    def remove_project(self, id_or_name: str) -> bool:
        with self._get_connection() as conn:
            cur = conn.execute(
                "DELETE FROM projects WHERE id = ? OR name = ?", (id_or_name, id_or_name)
            )
            return cur.rowcount > 0

    def _row_to_project(self, row: sqlite3.Row) -> Project:
        return Project(
            id=row["id"],
            name=row["name"],
            path=row["path"],
            description=row["description"],
            tech_stack=json.loads(row["tech_stack"] or "[]"),
            last_scanned_at=(
                datetime.fromisoformat(row["last_scanned_at"])
                if row["last_scanned_at"]
                else None
            ),
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    # ---------------------------------------------------------
    # Content Atom Operations
    # ---------------------------------------------------------

    def save_atom(self, atom: ContentAtom) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO content_atoms (id, project_id, atom_type, title, summary, evidence, tech_stack, potential_score, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title = excluded.title,
                    summary = excluded.summary,
                    evidence = excluded.evidence,
                    tech_stack = excluded.tech_stack,
                    potential_score = excluded.potential_score,
                    status = excluded.status
                """,
                (
                    atom.id,
                    atom.project_id,
                    atom.atom_type.value,
                    atom.title,
                    atom.summary,
                    atom.evidence.model_dump_json(),
                    json.dumps(atom.tech_stack),
                    atom.potential_score,
                    atom.status,
                    atom.created_at.isoformat(),
                ),
            )

    def get_atom(self, atom_id: str) -> Optional[ContentAtom]:
        with self._get_connection() as conn:
            cur = conn.execute("SELECT * FROM content_atoms WHERE id = ?", (atom_id,))
            row = cur.fetchone()
            if not row:
                return None
            return self._row_to_atom(row)

    def list_atoms(
        self, project_id: Optional[str] = None, status: Optional[str] = None
    ) -> List[ContentAtom]:
        query = "SELECT * FROM content_atoms WHERE 1=1"
        params = []
        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY potential_score DESC, created_at DESC"

        with self._get_connection() as conn:
            cur = conn.execute(query, params)
            return [self._row_to_atom(r) for r in cur.fetchall()]

    def update_atom_status(self, atom_id: str, status: str) -> None:
        with self._get_connection() as conn:
            conn.execute("UPDATE content_atoms SET status = ? WHERE id = ?", (status, atom_id))

    def _row_to_atom(self, row: sqlite3.Row) -> ContentAtom:
        ev_data = json.loads(row["evidence"])
        return ContentAtom(
            id=row["id"],
            project_id=row["project_id"],
            atom_type=AtomType(row["atom_type"]),
            title=row["title"],
            summary=row["summary"],
            evidence=EvidenceRecord(**ev_data),
            tech_stack=json.loads(row["tech_stack"] or "[]"),
            potential_score=row["potential_score"],
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    # ---------------------------------------------------------
    # Draft Operations
    # ---------------------------------------------------------

    def save_draft(self, draft: Draft) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO drafts (id, atom_id, project_id, platform, title, raw_content, humanized_content, humanizer_audit, status, published_url, published_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title = excluded.title,
                    raw_content = excluded.raw_content,
                    humanized_content = excluded.humanized_content,
                    humanizer_audit = excluded.humanizer_audit,
                    status = excluded.status,
                    published_url = excluded.published_url,
                    published_at = excluded.published_at,
                    updated_at = excluded.updated_at
                """,
                (
                    draft.id,
                    draft.atom_id,
                    draft.project_id,
                    draft.platform.value,
                    draft.title,
                    draft.raw_content,
                    draft.humanized_content,
                    json.dumps(draft.humanizer_audit),
                    draft.status.value,
                    draft.published_url,
                    draft.published_at.isoformat() if draft.published_at else None,
                    draft.created_at.isoformat(),
                    draft.updated_at.isoformat(),
                ),
            )

    def get_draft(self, draft_id: str) -> Optional[Draft]:
        with self._get_connection() as conn:
            cur = conn.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,))
            row = cur.fetchone()
            if not row:
                return None
            return self._row_to_draft(row)

    def list_drafts(
        self,
        project_id: Optional[str] = None,
        platform: Optional[Platform] = None,
        status: Optional[DraftStatus] = None,
    ) -> List[Draft]:
        query = "SELECT * FROM drafts WHERE 1=1"
        params = []
        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)
        if platform:
            query += " AND platform = ?"
            params.append(platform.value)
        if status:
            query += " AND status = ?"
            params.append(status.value)
        query += " ORDER BY updated_at DESC"

        with self._get_connection() as conn:
            cur = conn.execute(query, params)
            return [self._row_to_draft(r) for r in cur.fetchall()]

    def update_draft_content(self, draft_id: str, new_content: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE drafts SET humanized_content = ?, updated_at = ? WHERE id = ?",
                (new_content, now, draft_id),
            )

    def update_draft_status(
        self,
        draft_id: str,
        status: DraftStatus,
        published_url: Optional[str] = None,
    ) -> None:
        now = datetime.now(timezone.utc)
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE drafts 
                SET status = ?, 
                    published_url = coalesce(?, published_url), 
                    published_at = case when ? = 'published' then ? else published_at end,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    status.value,
                    published_url,
                    status.value,
                    now.isoformat(),
                    now.isoformat(),
                    draft_id,
                ),
            )

    def delete_draft(self, draft_id: str) -> bool:
        with self._get_connection() as conn:
            cur = conn.execute("DELETE FROM drafts WHERE id = ?", (draft_id,))
            return cur.rowcount > 0

    def _row_to_draft(self, row: sqlite3.Row) -> Draft:
        return Draft(
            id=row["id"],
            atom_id=row["atom_id"],
            project_id=row["project_id"],
            platform=Platform(row["platform"]),
            title=row["title"],
            raw_content=row["raw_content"],
            humanized_content=row["humanized_content"],
            humanizer_audit=json.loads(row["humanizer_audit"] or "{}"),
            status=DraftStatus(row["status"]),
            published_url=row["published_url"],
            published_at=(
                datetime.fromisoformat(row["published_at"])
                if row["published_at"]
                else None
            ),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    # ---------------------------------------------------------
    # Voice Sample Operations
    # ---------------------------------------------------------

    def save_voice_sample(self, sample: VoiceSample) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO voice_samples (id, title, content, analysis, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title = excluded.title,
                    content = excluded.content,
                    analysis = excluded.analysis
                """,
                (
                    sample.id,
                    sample.title,
                    sample.content,
                    json.dumps(sample.analysis),
                    sample.created_at.isoformat(),
                ),
            )

    def list_voice_samples(self) -> List[VoiceSample]:
        with self._get_connection() as conn:
            cur = conn.execute("SELECT * FROM voice_samples ORDER BY created_at DESC")
            return [
                VoiceSample(
                    id=r["id"],
                    title=r["title"],
                    content=r["content"],
                    analysis=json.loads(r["analysis"] or "{}"),
                    created_at=datetime.fromisoformat(r["created_at"]),
                )
                for r in cur.fetchall()
            ]

    def delete_voice_sample(self, sample_id: str) -> bool:
        with self._get_connection() as conn:
            cur = conn.execute("DELETE FROM voice_samples WHERE id = ?", (sample_id,))
            return cur.rowcount > 0
