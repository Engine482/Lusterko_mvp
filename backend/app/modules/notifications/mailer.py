"""Outbound email delivery for invites (TASK-6401..6406).

Mirrors the AI-parser strategy pattern (see `app/modules/ai/parser.py`):
- `StubMailer` records sent invites in-memory; default for dev/test, no IO.
- `SmtpMailer` talks to a real SMTP server via stdlib `smtplib` + STARTTLS.

Selection: `LUSTERKO_MAILER=stub|smtp|auto`. `auto` (default) picks `smtp` if
`SMTP_HOST` is set, otherwise `stub`. Tests can call `set_mailer()` to inject
a sentinel without touching env.

Errors never propagate to the caller. The admin invite endpoint must keep
working even if the SMTP server is misconfigured — the invite token is the
source of truth, the email is a delivery convenience (PRD §22.4 spirit).
"""

from __future__ import annotations

import logging
import os
import smtplib
from dataclasses import dataclass, field
from email.message import EmailMessage
from typing import Protocol

logger = logging.getLogger("lusterko.mailer")


# --- Public types -----------------------------------------------------------


@dataclass(frozen=True)
class InviteEmail:
    to_email: str
    to_full_name: str
    invite_url: str
    expires_at_iso: str


@dataclass(frozen=True)
class SendResult:
    ok: bool
    error: str | None = None


class Mailer(Protocol):
    name: str

    def send_invite(self, msg: InviteEmail) -> SendResult: ...


# --- Templating -------------------------------------------------------------


_SUBJECT = "Запрошення до Lusterko"

_PLAINTEXT_TEMPLATE = """\
Вітаємо, {full_name}!

Вас запрошено до системи Lusterko (моніторинг психологічного стану).

Щоб увійти, перейдіть за посиланням:
{invite_url}

Запрошення дійсне до {expires_at}.

Якщо ви не очікували цього листа — просто проігноруйте його.

— Команда Lusterko
"""

_HTML_TEMPLATE = """\
<!doctype html>
<html lang="uk">
<body style="font-family: -apple-system, Arial, sans-serif; line-height: 1.5;">
  <p>Вітаємо, {full_name}!</p>
  <p>Вас запрошено до системи <b>Lusterko</b> (моніторинг психологічного стану).</p>
  <p>Щоб увійти, перейдіть за посиланням:</p>
  <p><a href="{invite_url}">{invite_url}</a></p>
  <p style="color:#666; font-size: 13px;">Запрошення дійсне до {expires_at}.</p>
  <p style="color:#666; font-size: 13px;">
    Якщо ви не очікували цього листа — просто проігноруйте його.
  </p>
  <p>— Команда Lusterko</p>
</body>
</html>
"""


def _build_email_message(msg: InviteEmail, *, from_email: str) -> EmailMessage:
    em = EmailMessage()
    em["Subject"] = _SUBJECT
    em["From"] = from_email
    em["To"] = msg.to_email
    em.set_content(
        _PLAINTEXT_TEMPLATE.format(
            full_name=msg.to_full_name,
            invite_url=msg.invite_url,
            expires_at=msg.expires_at_iso,
        )
    )
    em.add_alternative(
        _HTML_TEMPLATE.format(
            full_name=msg.to_full_name,
            invite_url=msg.invite_url,
            expires_at=msg.expires_at_iso,
        ),
        subtype="html",
    )
    return em


# --- Strategies -------------------------------------------------------------


@dataclass
class StubMailer:
    name: str = "stub"
    sent: list[InviteEmail] = field(default_factory=list)

    def send_invite(self, msg: InviteEmail) -> SendResult:
        self.sent.append(msg)
        logger.info(
            "invite_email_stub_sent",
            extra={"to": msg.to_email, "invite_url": msg.invite_url},
        )
        return SendResult(ok=True)


@dataclass
class SmtpMailer:
    name: str = "smtp"
    host: str = ""
    port: int = 587
    username: str = ""
    password: str = ""
    use_tls: bool = True
    from_email: str = ""

    def send_invite(self, msg: InviteEmail) -> SendResult:
        em = _build_email_message(msg, from_email=self.from_email or self.username)
        try:
            with smtplib.SMTP(self.host, self.port, timeout=10) as s:
                s.ehlo()
                if self.use_tls:
                    s.starttls()
                    s.ehlo()
                if self.username:
                    s.login(self.username, self.password)
                s.send_message(em)
            return SendResult(ok=True)
        except Exception as err:  # noqa: BLE001 — mailer must never propagate
            logger.warning(
                "invite_email_smtp_failed",
                extra={"to": msg.to_email, "error": str(err)},
            )
            return SendResult(ok=False, error=str(err))


# --- Selection --------------------------------------------------------------


_MAILER: Mailer | None = None


def _build_from_env() -> Mailer:
    provider = os.environ.get("LUSTERKO_MAILER", "auto").lower()
    smtp_host = os.environ.get("SMTP_HOST", "").strip()
    if provider == "stub":
        return StubMailer()
    if provider == "smtp" or (provider == "auto" and smtp_host):
        if not smtp_host:
            return StubMailer()
        return SmtpMailer(
            host=smtp_host,
            port=int(os.environ.get("SMTP_PORT", "587")),
            username=os.environ.get("SMTP_USER", ""),
            password=os.environ.get("SMTP_PASSWORD", ""),
            use_tls=os.environ.get("SMTP_USE_TLS", "true").lower() != "false",
            from_email=os.environ.get("INVITE_FROM_EMAIL", ""),
        )
    return StubMailer()


def get_mailer() -> Mailer:
    global _MAILER
    if _MAILER is None:
        _MAILER = _build_from_env()
    return _MAILER


def set_mailer(mailer: Mailer | None) -> None:
    """Test hook. `None` resets so the next `get_mailer()` rebuilds from env."""

    global _MAILER
    _MAILER = mailer


def build_invite_url(base_url: str, token: str) -> str:
    return f"{base_url.rstrip('/')}/invite?token={token}"
