"""Twitter Web Intent bridge with automated system clipboard image copy."""

import shutil
import subprocess
import urllib.parse
from pathlib import Path
from typing import Optional

from lore.publishing.base import PublishResult


def copy_image_to_clipboard(image_path: Path) -> bool:
    """Copies PNG image to system clipboard using native desktop utilities."""
    if not image_path.is_file():
        return False

    # Linux wl-copy (Wayland)
    if shutil.which("wl-copy"):
        try:
            with open(image_path, "rb") as f:
                subprocess.run(["wl-copy", "--type", "image/png"], stdin=f, check=True)
                return True
        except Exception:
            pass

    # Linux xclip (X11)
    if shutil.which("xclip"):
        try:
            subprocess.run(
                ["xclip", "-selection", "clipboard", "-t", "image/png", "-i", str(image_path)],
                check=True,
            )
            return True
        except Exception:
            pass

    # macOS pbcopy / osascript
    if shutil.which("osascript"):
        try:
            cmd = f'set the clipboard to (read (POSIX file "{image_path.resolve()}") as «class PNGf»)'
            subprocess.run(["osascript", "-e", cmd], check=True)
            return True
        except Exception:
            pass

    return False


class TwitterBridgePublisher:
    """Generates Twitter Web Intent URLs and copies diff card PNGs to clipboard."""

    @classmethod
    def publish(
        cls,
        content: str,
        image_path: Optional[str] = None,
    ) -> PublishResult:
        encoded_text = urllib.parse.quote(content)
        intent_url = f"https://twitter.com/intent/tweet?text={encoded_text}"

        clipboard_copied = False
        if image_path:
            p = Path(image_path)
            clipboard_copied = copy_image_to_clipboard(p)

        return PublishResult(
            success=True,
            platform="twitter",
            published_url=intent_url,
            error=None if clipboard_copied else "Image could not be auto-copied to clipboard",
        )
