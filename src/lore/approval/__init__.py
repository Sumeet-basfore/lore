"""Lore Approval Gateways & Local Web Dashboard."""

from lore.approval.discord_gateway import send_discord_approval_card
from lore.approval.local_web import LoreWebReviewServer, run_local_web_server
from lore.approval.slack_gateway import send_slack_approval_card
from lore.approval.telegram_gateway import send_telegram_approval_card

__all__ = [
    "LoreWebReviewServer",
    "run_local_web_server",
    "send_slack_approval_card",
    "send_discord_approval_card",
    "send_telegram_approval_card",
]