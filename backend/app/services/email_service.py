"""
Email integration (Agent 1 input source).

Reads unread messages from a real IMAP inbox and returns each as plain
text (subject + body) for Agent 1 (Extractor) to process — exactly like
a pasted meeting transcript.

Works with Gmail (use an "App Password", not your normal password:
https://myaccount.google.com/apppasswords), Outlook, or any IMAP server.

Uses only Python's built-in `imaplib` / `email` — no extra dependency.
"""
import imaplib
import email as email_lib
from email.header import decode_header
from app.config import settings


class EmailNotConfigured(Exception):
    pass


def _require_config():
    if not (settings.IMAP_HOST and settings.IMAP_USER and settings.IMAP_PASSWORD):
        raise EmailNotConfigured(
            "Email is not configured. Set IMAP_HOST, IMAP_USER, and "
            "IMAP_PASSWORD in your .env file. For Gmail, use an App "
            "Password: https://myaccount.google.com/apppasswords"
        )


def test_connection() -> dict:
    _require_config()
    conn = imaplib.IMAP4_SSL(settings.IMAP_HOST, settings.IMAP_PORT)
    try:
        conn.login(settings.IMAP_USER, settings.IMAP_PASSWORD)
        status, mailboxes = conn.select(settings.IMAP_MAILBOX, readonly=True)
        return {"connected": True, "mailbox": settings.IMAP_MAILBOX, "status": status}
    finally:
        conn.logout()


def _decode(value) -> str:
    if not value:
        return ""
    parts = decode_header(value)
    decoded = ""
    for text, enc in parts:
        if isinstance(text, bytes):
            decoded += text.decode(enc or "utf-8", errors="ignore")
        else:
            decoded += text
    return decoded


def _extract_body(msg) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition") or "")
            if content_type == "text/plain" and "attachment" not in disposition:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="ignore")
        return ""
    payload = msg.get_payload(decode=True)
    if not payload:
        return ""
    charset = msg.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="ignore")


def fetch_unread_emails(max_results: int = 25, mark_as_read: bool = False) -> list[dict]:
    """
    Fetch unread emails from the configured IMAP inbox and return each as
    {"subject": "...", "from": "...", "text": "<subject + body>"}.

    By default leaves messages marked unread (safe to re-run). Pass
    mark_as_read=True to mark processed messages as seen, so a
    scheduled sync only ever picks up genuinely new mail.
    """
    _require_config()
    conn = imaplib.IMAP4_SSL(settings.IMAP_HOST, settings.IMAP_PORT)
    results = []
    try:
        conn.login(settings.IMAP_USER, settings.IMAP_PASSWORD)
        conn.select(settings.IMAP_MAILBOX)

        status, data = conn.search(None, "UNSEEN")
        if status != "OK":
            return []

        ids = data[0].split()[-max_results:]  # most recent N unread
        for msg_id in ids:
            fetch_mode = "(RFC822)" if mark_as_read else "(BODY.PEEK[])"
            status, msg_data = conn.fetch(msg_id, fetch_mode)
            if status != "OK" or not msg_data or not msg_data[0]:
                continue

            raw = msg_data[0][1]
            msg = email_lib.message_from_bytes(raw)

            subject = _decode(msg.get("Subject"))
            sender = _decode(msg.get("From"))
            body = _extract_body(msg).strip()

            text = subject
            if body:
                text += f"\n\n{body}"

            results.append({"subject": subject, "from": sender, "text": text.strip()})

    finally:
        conn.logout()

    return results
