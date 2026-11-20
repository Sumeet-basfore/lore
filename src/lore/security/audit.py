"""Audit logger for tracking DLP compliance scans in SQLite."""

import uuid
from typing import Optional

from lore.core.database import Database
from lore.core.models import DLPAuditLog, utc_now
from lore.security.dlp_scanner import DLPScanResult


class DLPAuditLogger:
    """Immutable audit logging for DLP scan events."""

    @classmethod
    def log_scan_event(
        cls,
        db: Database,
        target_type: str,  # 'commit', 'atom', 'draft'
        target_id: str,
        scan_result: DLPScanResult,
        draft_id: Optional[str] = None,
    ) -> DLPAuditLog:
        audit_record = DLPAuditLog(
            id=f"dlp_{uuid.uuid4().hex[:12]}",
            target_type=target_type,
            target_id=target_id,
            draft_id=draft_id,
            scanned_at=utc_now(),
            rules_evaluated=scan_result.rules_evaluated,
            violations_detected=len(scan_result.violations),
            masked_entities_json={"violations": scan_result.violations},
            highest_entropy_score=scan_result.highest_entropy,
            status=scan_result.status,
        )
        db.log_dlp_audit(audit_record)
        return audit_record
