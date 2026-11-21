"""SQLite database storage layer for Lore."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator, List, Optional

from lore.config import get_lore_home
from lore.core.exceptions import DatabaseError
from lore.core.models import (
    AtomType,
    ContentAtom,
    DLPAuditLog,
    Draft,
    DraftStatus,
    EvidenceRecord,
    Platform,
    Project,
    PublishQueueItem,
    VoiceSample,
)


class Database:
    """Manages SQLite persistence for projects, content atoms, drafts, voice samples, DLP audits, and publish queues."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            self.db_path = get_lore_home() / "lore.db"
        else:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Initializes tables, indexes, and runs pending migrations."""
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
                    card_image_path TEXT,
                    dlp_status TEXT DEFAULT 'clean',
                    dlp_audit_json TEXT,
                    scheduled_for TEXT,
                    channel_target TEXT,
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

                CREATE TABLE IF NOT EXISTS dlp_audit_logs (
                    id TEXT PRIMARY KEY,
                    target_type TEXT NOT NULL, -- 'commit', 'atom', 'draft'
                    target_id TEXT NOT NULL,
                    draft_id TEXT,
                    scanned_at TEXT NOT NULL,
                    rules_evaluated INTEGER NOT NULL,
                    violations_detected INTEGER NOT NULL,
                    masked_entities_json TEXT,
                    highest_entropy_score REAL,
                    status TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS publish_queue (
                    id TEXT PRIMARY KEY,
                    draft_id TEXT NOT NULL REFERENCES drafts(id) ON DELETE CASCADE,
                    platform TEXT NOT NULL,
                    scheduled_time TEXT NOT NULL,
                    attempts INTEGER DEFAULT 0,
                    last_error TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_atoms_project ON content_atoms(project_id);
                CREATE INDEX IF NOT EXISTS idx_atoms_status ON content_atoms(status);
                CREATE INDEX IF NOT EXISTS idx_drafts_project ON drafts(project_id);
                CREATE INDEX IF NOT EXISTS idx_drafts_status ON drafts(status);
                CREATE INDEX IF NOT EXISTS idx_drafts_platform ON drafts(platform);
                CREATE INDEX IF NOT EXISTS idx_dlp_target ON dlp_audit_logs(target_type, target_id);
                CREATE INDEX IF NOT EXISTS idx_publish_queue_status ON publish_queue(status, scheduled_time);
                """
            )
            self._migrate_v1_to_v2(conn)

    def _migrate_v1_to_v2(self, conn: sqlite3.Connection) -> None:
        """Idempotently ensures schema v2 columns and tables exist and updates PRAGMA user_version."""
        cur = conn.execute("PRAGMA user_version;")
        version = cur.fetchone()[0]

        cur = conn.execute("PRAGMA table_info(drafts);")
        existing_cols = {row["name"] for row in cur.fetchall()}

        # Add missing columns to drafts if migrating from v1
        new_columns = [
            ("card_image_path", "TEXT"),
            ("dlp_status", "TEXT DEFAULT 'clean'"),
            ("dlp_audit_json", "TEXT"),
            ("scheduled_for", "TEXT"),
            ("channel_target", "TEXT"),
        ]
        for col_name, col_type in new_columns:
            if col_name not in existing_cols:
                conn.execute(f"ALTER TABLE drafts ADD COLUMN {col_name} {col_type};")

        # Create dlp_audit_logs and publish_queue if not exists
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS dlp_audit_logs (
                id TEXT PRIMARY KEY,
                target_type TEXT NOT NULL,
                target_id TEXT NOT NULL,
                draft_id TEXT,
                scanned_at TEXT NOT NULL,
                rules_evaluated INTEGER NOT NULL,
                violations_detected INTEGER NOT NULL,
                masked_entities_json TEXT,
                highest_entropy_score REAL,
                status TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS publish_queue (
                id TEXT PRIMARY KEY,
                draft_id TEXT NOT NULL REFERENCES drafts(id) ON DELETE CASCADE,
                platform TEXT NOT NULL,
                scheduled_time TEXT NOT NULL,
                attempts INTEGER DEFAULT 0,
                last_error TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_dlp_target ON dlp_audit_logs(target_type, target_id);
            CREATE INDEX IF NOT EXISTS idx_publish_queue_status ON publish_queue(status, scheduled_time);
            """
        )

        if version < 2:
            conn.execute("PRAGMA user_version = 2;")

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

    def get_project_by_path(self, path: Path | str) -> Optional[Project]:
        """Find a project by its canonical filesystem path."""
        normalized_path = str(Path(path).expanduser().resolve())
        with self._get_connection() as conn:
            cur = conn.execute("SELECT * FROM projects WHERE path = ?", (normalized_path,))
            row = cur.fetchone()
            if row:
                return self._row_to_project(row)

            # Older databases may contain paths written before path resolution was applied.
            cur = conn.execute("SELECT * FROM projects")
            for candidate in cur.fetchall():
                try:
                    candidate_path = str(Path(candidate["path"]).expanduser().resolve())
                except (OSError, RuntimeError):
                    continue
                if candidate_path == normalized_path:
                    return self._row_to_project(candidate)
        return None

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
                INSERT INTO drafts (
                    id, atom_id, project_id, platform, title, raw_content, 
                    humanized_content, humanizer_audit, status, published_url, 
                    published_at, card_image_path, dlp_status, dlp_audit_json, 
                    scheduled_for, channel_target, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title = excluded.title,
                    raw_content = excluded.raw_content,
                    humanized_content = excluded.humanized_content,
                    humanizer_audit = excluded.humanizer_audit,
                    status = excluded.status,
                    published_url = excluded.published_url,
                    published_at = excluded.published_at,
                    card_image_path = excluded.card_image_path,
                    dlp_status = excluded.dlp_status,
                    dlp_audit_json = excluded.dlp_audit_json,
                    scheduled_for = excluded.scheduled_for,
                    channel_target = excluded.channel_target,
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
                    draft.card_image_path,
                    draft.dlp_status,
                    json.dumps(draft.dlp_audit_json) if draft.dlp_audit_json else None,
                    draft.scheduled_for.isoformat() if draft.scheduled_for else None,
                    draft.channel_target,
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
        keys = row.keys()
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
            card_image_path=row["card_image_path"] if "card_image_path" in keys else None,
            dlp_status=row["dlp_status"] if "dlp_status" in keys and row["dlp_status"] else "clean",
            dlp_audit_json=(
                json.loads(row["dlp_audit_json"])
                if "dlp_audit_json" in keys and row["dlp_audit_json"]
                else None
            ),
            scheduled_for=(
                datetime.fromisoformat(row["scheduled_for"])
                if "scheduled_for" in keys and row["scheduled_for"]
                else None
            ),
            channel_target=row["channel_target"] if "channel_target" in keys else None,
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

    # ---------------------------------------------------------
    # DLP Audit Log Operations (Phase 0 / Phase 2)
    # ---------------------------------------------------------

    def log_dlp_audit(self, audit: DLPAuditLog) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO dlp_audit_logs (
                    id, target_type, target_id, draft_id, scanned_at,
                    rules_evaluated, violations_detected, masked_entities_json,
                    highest_entropy_score, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit.id,
                    audit.target_type,
                    audit.target_id,
                    audit.draft_id,
                    audit.scanned_at.isoformat(),
                    audit.rules_evaluated,
                    audit.violations_detected,
                    json.dumps(audit.masked_entities_json) if audit.masked_entities_json else None,
                    audit.highest_entropy_score,
                    audit.status,
                ),
            )

    def get_dlp_audits(
        self,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        draft_id: Optional[str] = None,
    ) -> List[DLPAuditLog]:
        query = "SELECT * FROM dlp_audit_logs WHERE 1=1"
        params = []
        if target_type:
            query += " AND target_type = ?"
            params.append(target_type)
        if target_id:
            query += " AND target_id = ?"
            params.append(target_id)
        if draft_id:
            query += " AND draft_id = ?"
            params.append(draft_id)
        query += " ORDER BY scanned_at DESC"

        with self._get_connection() as conn:
            cur = conn.execute(query, params)
            return [
                DLPAuditLog(
                    id=r["id"],
                    target_type=r["target_type"],
                    target_id=r["target_id"],
                    draft_id=r["draft_id"],
                    scanned_at=datetime.fromisoformat(r["scanned_at"]),
                    rules_evaluated=r["rules_evaluated"],
                    violations_detected=r["violations_detected"],
                    masked_entities_json=json.loads(r["masked_entities_json"]) if r["masked_entities_json"] else None,
                    highest_entropy_score=r["highest_entropy_score"] or 0.0,
                    status=r["status"],
                )
                for r in cur.fetchall()
            ]

    # ---------------------------------------------------------
    # Publish Queue Operations (Phase 0 / Phase 6)
    # ---------------------------------------------------------

    def enqueue_publish(self, item: PublishQueueItem) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO publish_queue (id, draft_id, platform, scheduled_time, attempts, last_error, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    attempts = publish_queue.attempts + 1,
                    scheduled_time = excluded.scheduled_time,
                    last_error = excluded.last_error,
                    status = excluded.status
                """,
                (
                    item.id,
                    item.draft_id,
                    item.platform.value,
                    item.scheduled_time.isoformat(),
                    item.attempts,
                    item.last_error,
                    item.status,
                    item.created_at.isoformat(),
                ),
            )

    def get_pending_publishes(self, before_time: Optional[datetime] = None) -> List[PublishQueueItem]:
        query = "SELECT * FROM publish_queue WHERE status = 'pending'"
        params = []
        if before_time:
            query += " AND scheduled_time <= ?"
            params.append(before_time.isoformat())
        query += " ORDER BY scheduled_time ASC"

        with self._get_connection() as conn:
            cur = conn.execute(query, params)
            return [
                PublishQueueItem(
                    id=r["id"],
                    draft_id=r["draft_id"],
                    platform=Platform(r["platform"]),
                    scheduled_time=datetime.fromisoformat(r["scheduled_time"]),
                    attempts=r["attempts"],
                    last_error=r["last_error"],
                    status=r["status"],
                    created_at=datetime.fromisoformat(r["created_at"]),
                )
                for r in cur.fetchall()
            ]

    def update_publish_status(self, item_id: str, status: str, error: Optional[str] = None) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE publish_queue 
                SET status = ?, attempts = attempts + 1, last_error = ?
                WHERE id = ?
                """,
                (status, error, item_id),
            )
