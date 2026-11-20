"""Draft export utilities for Markdown and JSON."""

import json
from pathlib import Path
from typing import List
from lore.core.models import Draft


class DraftExporter:
    """Exports approved or selected drafts to disk."""

    @classmethod
    def export(
        cls,
        drafts: List[Draft],
        output_dir: Path,
        format_type: str = "markdown",
    ) -> List[Path]:
        out = Path(output_dir).resolve()
        out.mkdir(parents=True, exist_ok=True)
        exported_files: List[Path] = []

        if format_type.lower() == "json":
            json_file = out / "lore_drafts_export.json"
            data = [d.model_dump(mode="json") for d in drafts]
            json_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
            exported_files.append(json_file)
            return exported_files

        # Default: Markdown files
        for draft in drafts:
            safe_title = (draft.title or "untitled").lower()
            safe_title = "".join(c if c.isalnum() else "_" for c in safe_title)[:40].strip("_")
            filename = f"{draft.platform.value}_{safe_title}_{draft.id[:8]}.md"
            target_path = out / filename

            frontmatter = [
                "---",
                f"id: {draft.id}",
                f"project: {draft.project_id}",
                f"platform: {draft.platform.value}",
                f"status: {draft.status.value}",
                f"created_at: {draft.created_at.isoformat()}",
                "---",
                "",
                draft.humanized_content,
                "",
            ]

            target_path.write_text("\n".join(frontmatter), encoding="utf-8")
            exported_files.append(target_path)

        return exported_files
