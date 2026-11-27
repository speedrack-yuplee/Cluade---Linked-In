#!/usr/bin/env python3
"""Send a generated post and its image to a Telegram chat.

Reads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from the environment; both are
repository secrets, never committed. Uses the standard library only, so the
workflow needs no extra install step.

    python scripts/send_telegram.py out/post.txt out/post.png
    python scripts/send_telegram.py note.txt

The image is optional: a plain note goes out as text alone.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

API = "https://api.telegram.org/bot{token}/{method}"
CAPTION_LIMIT = 1024


def _post(token: str, method: str, fields: dict[str, str], files: dict[str, Path] | None = None):
    """One multipart request. Telegram accepts urlencoded too, but a photo
    upload has to be multipart, so both paths use the same encoder."""
    boundary = uuid.uuid4().hex
    body = bytearray()
    for name, value in fields.items():
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
        body += f"{value}\r\n".encode()
    for name, path in (files or {}).items():
        body += f"--{boundary}\r\n".encode()
        body += (
            f'Content-Disposition: form-data; name="{name}"; filename="{path.name}"\r\n'
            f"Content-Type: application/octet-stream\r\n\r\n"
        ).encode()
        body += path.read_bytes() + b"\r\n"
    body += f"--{boundary}--\r\n".encode()

    request = urllib.request.Request(
        API.format(token=token, method=method),
        data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        # The token must never reach the log, and Telegram echoes the URL.
        raise SystemExit(f"telegram {method} failed: HTTP {exc.code} {detail[:400]}") from None


def main(argv: list[str]) -> int:
    if not 1 <= len(argv) <= 2:
        print(__doc__)
        return 64

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        raise SystemExit("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set")

    text_path = Path(argv[0])
    image_path = Path(argv[1]) if len(argv) == 2 else None
    text = text_path.read_text(encoding="utf-8").strip()

    if image_path is not None:
        _post(
            token,
            "sendPhoto",
            {"chat_id": chat_id, "caption": "LinkedIn draft"},
            {"photo": image_path},
        )
    # The post goes as its own message so it can be copied in one tap, and so
    # a post longer than a photo caption is never truncated.
    for chunk in (text[i : i + 4000] for i in range(0, len(text), 4000)):
        _post(token, "sendMessage", {"chat_id": chat_id, "text": chunk})

    print(f"sent {len(text)} characters" + (f" and {image_path.name}" if image_path else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
