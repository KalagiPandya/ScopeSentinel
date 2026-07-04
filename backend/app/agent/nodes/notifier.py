"""
Agent 8 — Notification Agent

Final agent in the pipeline. Looks at the risk level of detected changes
(or the PR review recommendation) and decides which channels to notify.

Channel rules:
  - low / medium risk     -> dashboard only
  - high risk              -> dashboard + email
  - critical risk          -> dashboard + email + slack

This Day 10 version focuses on DECIDING and FORMATTING notifications and
logging them to the alerts table. Actual Slack/email delivery uses
lightweight stubs (print + optional webhook) so the pipeline works
out-of-the-box without requiring Slack/SMTP setup, but is easy to wire
to real services later by filling in SLACK_WEBHOOK_URL / SMTP settings.
"""
from typing import List, Dict
from app.agent.state import AgentState


def _channels_for_risk(risk_level: str) -> List[str]:
    if risk_level == "critical":
        return ["dashboard", "email", "slack"]
    if risk_level == "high":
        return ["dashboard", "email"]
    return ["dashboard"]


def _send_slack(message: str) -> bool:
    """Send to Slack via webhook if configured. Returns True if sent."""
    import httpx
    from app.config import settings

    webhook = getattr(settings, "SLACK_WEBHOOK_URL", "") or ""
    if not webhook:
        print(f"[Agent 8 - Slack STUB] {message}")
        return False

    try:
        httpx.post(webhook, json={"text": message}, timeout=5.0)
        return True
    except Exception as e:
        print(f"[Agent 8 - Slack ERROR] {e}")
        return False


def _send_email(subject: str, body: str, to: str) -> bool:
    """Send email via SMTP if configured. Returns True if sent."""
    from app.config import settings

    smtp_host = getattr(settings, "SMTP_HOST", "") or ""
    if not smtp_host:
        print(f"[Agent 8 - Email STUB] To: {to} | Subject: {subject}\n{body}")
        return False

    try:
        import smtplib
        from email.mime.text import MIMEText

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = getattr(settings, "SMTP_FROM", "scopesentinel@example.com")
        msg["To"] = to

        with smtplib.SMTP(smtp_host, getattr(settings, "SMTP_PORT", 587)) as server:
            if getattr(settings, "SMTP_USER", ""):
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"[Agent 8 - Email ERROR] {e}")
        return False


def notifier_node(state: AgentState) -> AgentState:
    """
    Reads state['detected_changes'] (each with 'risk').
    Writes state['notifications'] — list of {change_index, channels, sent}.

    Also dispatches to Slack/Email stubs based on risk level.
    Dashboard notifications are always "sent" (the dashboard reads
    from the alerts table directly via WebSocket/polling).
    """
    changes = state.get("detected_changes", [])
    errors = list(state.get("errors", []))
    notifications = []

    for idx, change in enumerate(changes):
        risk = change.get("risk", {})
        risk_level = risk.get("risk_level", "low")
        channels = _channels_for_risk(risk_level)

        sent_channels = []
        message = (
            f"[{risk_level.upper()}] Requirement change detected: "
            f"\"{change.get('new_text', '')[:100]}\" "
            f"(risk score {risk.get('risk_score', 0)}/100). "
            f"{risk.get('recommended_action', '')}"
        )

        if "dashboard" in channels:
            sent_channels.append("dashboard")  # always available via DB

        if "slack" in channels:
            if _send_slack(message):
                sent_channels.append("slack")
            else:
                sent_channels.append("slack_stub")

        if "email" in channels:
            subject = f"ScopeSentinel Alert: {risk_level.upper()} risk requirement change"
            if _send_email(subject, message, to="pm@scopesentinel.com"):
                sent_channels.append("email")
            else:
                sent_channels.append("email_stub")

        notifications.append({
            "change_index": idx,
            "risk_level": risk_level,
            "channels": channels,
            "sent_channels": sent_channels,
            "message": message,
        })

    return {**state, "notifications": notifications, "status": "done", "errors": errors}
