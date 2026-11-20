"""Discord rich embed approval gateway via httpx (zero-vendor-SDK)."""

from typing import Any, Dict, Optional
import httpx

from lore.core.models import Draft


def build_discord_payload(
    draft: Draft,
    card_image_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Constructs a Discord webhook payload with embed and action buttons."""
    embed: Dict[str, Any] = {
        "title": f"Lore Review: {draft.title or 'Untitled Draft'}",
        "description": f"```{draft.humanized_content[:2000]}```",
        "color": 0x3FB950 if draft.status.value == "approved" else 0x58A6FF,
        "fields": [
            {"name": "Platform", "value": draft.platform.value.upper(), "inline": True},
            {"name": "Status", "value": draft.status.value, "inline": True},
            {"name": "Draft ID", "value": draft.id, "inline": True},
        ],
    }

    if card_image_url:
        embed["image"] = {"url": card_image_url}

    return {"embeds": [embed]}


def send_discord_approval_card(
    webhook_url: str,
    draft: Draft,
    card_image_url: Optional[str] = None,
) -> bool:
    """Dispatches a Discord webhook embed."""
    payload = build_discord_payload(draft, card_image_url=card_image_url)
    try:
        resp = httpx.post(webhook_url, json=payload, timeout=10.0)
        return resp.status_code in (200, 204)
    except Exception:
        return False