"""Slack Block Kit approval gateway via httpx (zero-vendor-SDK)."""

from typing import Any, Dict, List, Optional
import httpx

from lore.core.models import Draft


def build_slack_blocks(
    draft: Draft,
    card_image_url: Optional[str] = None,
    commit_url: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Constructs native Slack Block Kit blocks for draft review."""
    blocks: List[Dict[str, Any]] = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"New Draft Ready: {draft.title or 'Untitled'}",
                "emoji": False,
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"*Platform:* {draft.platform.value.upper()} | *Status:* {draft.status.value}",
                }
            ],
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"```{draft.humanized_content[:2800]}```",
            },
        },
    ]

    if card_image_url:
        blocks.append({
            "type": "image",
            "image_url": card_image_url,
            "alt_text": "Code diff card",
        })

    # Interactive action buttons
    blocks.append({
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Approve & Schedule"},
                "style": "primary",
                "value": draft.id,
                "action_id": "lore_approve",
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Approve with Edit"},
                "value": draft.id,
                "action_id": "lore_edit",
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Dismiss"},
                "style": "danger",
                "value": draft.id,
                "action_id": "lore_reject",
            },
        ],
    })

    return blocks


def send_slack_approval_card(
    webhook_url: str,
    draft: Draft,
    card_image_url: Optional[str] = None,
    commit_url: Optional[str] = None,
) -> bool:
    """Dispatches a Slack Block Kit interactive card to a webhook URL."""
    if not (
        webhook_url.startswith("https://hooks.slack.com/services/")
        or webhook_url.startswith("https://hooks.slack.com/workflows/")
    ):
        return False

    blocks = build_slack_blocks(draft, card_image_url=card_image_url, commit_url=commit_url)
    payload = {"blocks": blocks}

    try:
        resp = httpx.post(webhook_url, json=payload, timeout=10.0)
        return resp.status_code == 200
    except Exception:
        return False