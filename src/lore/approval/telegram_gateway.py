"""Telegram Bot 1-tap approval listener and dispatcher via httpx."""

from typing import Any, Dict, Optional
import httpx

from lore.core.models import Draft


def build_telegram_payload(
    chat_id: str,
    draft: Draft,
    card_image_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Constructs Telegram sendMessage payload with inline keyboard markup."""
    text = (
        f"<b>Lore Review:</b> {draft.title or 'Untitled'}\n"
        f"<b>Platform:</b> {draft.platform.value.upper()}\n"
        f"<b>Status:</b> {draft.status.value}\n\n"
        f"<pre>{draft.humanized_content[:3500]}</pre>"
    )

    inline_keyboard = [
        [
            {"text": "Approve", "callback_data": f"approve_{draft.id}"},
            {"text": "Reject", "callback_data": f"reject_{draft.id}"},
        ]
    ]

    return {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": {"inline_keyboard": inline_keyboard},
    }


def send_telegram_approval_card(
    bot_token: str,
    chat_id: str,
    draft: Draft,
    card_image_url: Optional[str] = None,
) -> bool:
    """Dispatches a Telegram message with inline approval buttons."""
    payload = build_telegram_payload(chat_id, draft, card_image_url=card_image_url)
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        resp = httpx.post(url, json=payload, timeout=10.0)
        return resp.status_code == 200
    except Exception:
        return False