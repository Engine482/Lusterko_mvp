"""Outbound email delivery for invites and password resets.

Mirrors the AI-parser strategy pattern (see `app/modules/ai/parser.py`):
- `StubMailer` records sent messages in-memory; default for dev/test, no IO.
- `SmtpMailer` talks to a real SMTP server via stdlib `smtplib` + STARTTLS.

Selection: `LUSTERKO_MAILER=stub|smtp|auto`. `auto` (default) picks `smtp` if
`SMTP_HOST` is set, otherwise `stub`. Tests can call `set_mailer()` to inject
a sentinel without touching env.

Errors never propagate to the caller. Invite creation and password-reset
issuance must keep working even if the SMTP server is misconfigured — the
token is the source of truth, the email is a delivery convenience.
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
class PasswordResetEmail:
    to_email: str
    to_full_name: str
    reset_url: str
    expires_at_iso: str


@dataclass(frozen=True)
class DemoRegistrationEmail:
    to_email: str
    confirm_url: str
    expires_at_iso: str


@dataclass(frozen=True)
class SendResult:
    ok: bool
    error: str | None = None


class Mailer(Protocol):
    name: str

    def send_invite(self, msg: InviteEmail) -> SendResult: ...
    def send_password_reset(self, msg: PasswordResetEmail) -> SendResult: ...
    def send_demo_registration(self, msg: DemoRegistrationEmail) -> SendResult: ...


# --- Templating -------------------------------------------------------------


_INVITE_SUBJECT = "Запрошення до Lusterko"

_INVITE_PLAINTEXT = """\
Вітаємо, {full_name}!

Вас запрошено до системи Lusterko (моніторинг психологічного стану).

Щоб встановити пароль і увійти, перейдіть за посиланням:
{invite_url}

Запрошення дійсне до {expires_at}.

Якщо ви не очікували цього листа — просто проігноруйте його.

— Команда Lusterko
"""

_INVITE_HTML = """\
<!doctype html>
<html lang="uk">
<body style="font-family: -apple-system, Arial, sans-serif; line-height: 1.5;">
  <p>Вітаємо, {full_name}!</p>
  <p>Вас запрошено до системи <b>Lusterko</b> (моніторинг психологічного стану).</p>
  <p>Щоб встановити пароль і увійти, перейдіть за посиланням:</p>
  <p><a href="{invite_url}">{invite_url}</a></p>
  <p style="color:#666; font-size: 13px;">Запрошення дійсне до {expires_at}.</p>
  <p style="color:#666; font-size: 13px;">
    Якщо ви не очікували цього листа — просто проігноруйте його.
  </p>
  <p>— Команда Lusterko</p>
</body>
</html>
"""


_RESET_SUBJECT = "Скидання паролю в Lusterko"

_RESET_PLAINTEXT = """\
Вітаємо, {full_name}!

Ми отримали запит на скидання паролю до вашого акаунта в Lusterko.

Щоб задати новий пароль, перейдіть за посиланням:
{reset_url}

Посилання дійсне до {expires_at}.

Якщо ви не запитували скидання — проігноруйте цей лист, ваш пароль не змінився.

— Команда Lusterko
"""

_RESET_HTML = """\
<!doctype html>
<html lang="uk">
<body style="font-family: -apple-system, Arial, sans-serif; line-height: 1.5;">
  <p>Вітаємо, {full_name}!</p>
  <p>Ми отримали запит на скидання паролю до вашого акаунта в <b>Lusterko</b>.</p>
  <p>Щоб задати новий пароль, перейдіть за посиланням:</p>
  <p><a href="{reset_url}">{reset_url}</a></p>
  <p style="color:#666; font-size: 13px;">Посилання дійсне до {expires_at}.</p>
  <p style="color:#666; font-size: 13px;">
    Якщо ви не запитували скидання — проігноруйте цей лист, ваш пароль не змінився.
  </p>
  <p>— Команда Lusterko</p>
</body>
</html>
"""


_DEMO_REG_SUBJECT = "Підтвердіть реєстрацію в Lusterko (demo)"

_DEMO_REG_PLAINTEXT = """\
Вітаємо!

Ми отримали запит на реєстрацію в demo-режимі Lusterko (моніторинг
психологічного стану особового складу).

Щоб задати пароль і завершити створення тестового акаунта, перейдіть за
посиланням:
{confirm_url}

Посилання дійсне до {expires_at}.

Якщо ви не запитували реєстрацію — просто проігноруйте цей лист.

— Команда Lusterko
"""

_DEMO_REG_HTML = """\
<!doctype html>
<html lang="uk">
<body style="font-family: -apple-system, Arial, sans-serif; line-height: 1.5;">
  <p>Вітаємо!</p>
  <p>Ми отримали запит на реєстрацію в demo-режимі <b>Lusterko</b>
  (моніторинг психологічного стану особового складу).</p>
  <p>Щоб задати пароль і завершити створення тестового акаунта, перейдіть
  за посиланням:</p>
  <p><a href="{confirm_url}">{confirm_url}</a></p>
  <p style="color:#666; font-size: 13px;">Посилання дійсне до {expires_at}.</p>
  <p style="color:#666; font-size: 13px;">
    Якщо ви не запитували реєстрацію — просто проігноруйте цей лист.
  </p>
  <p>— Команда Lusterko</p>
</body>
</html>
"""


def _build_demo_registration_message(
    msg: DemoRegistrationEmail, *, from_email: str
) -> EmailMessage:
    em = EmailMessage()
    em["Subject"] = _DEMO_REG_SUBJECT
    em["From"] = from_email
    em["To"] = msg.to_email
    em.set_content(
        _DEMO_REG_PLAINTEXT.format(
            confirm_url=msg.confirm_url,
            expires_at=msg.expires_at_iso,
        )
    )
    em.add_alternative(
        _DEMO_REG_HTML.format(
            confirm_url=msg.confirm_url,
            expires_at=msg.expires_at_iso,
        ),
        subtype="html",
    )
    return em


def _build_invite_message(msg: InviteEmail, *, from_email: str) -> EmailMessage:
    em = EmailMessage()
    em["Subject"] = _INVITE_SUBJECT
    em["From"] = from_email
    em["To"] = msg.to_email
    em.set_content(
        _INVITE_PLAINTEXT.format(
            full_name=msg.to_full_name,
            invite_url=msg.invite_url,
            expires_at=msg.expires_at_iso,
        )
    )
    em.add_alternative(
        _INVITE_HTML.format(
            full_name=msg.to_full_name,
            invite_url=msg.invite_url,
            expires_at=msg.expires_at_iso,
        ),
        subtype="html",
    )
    return em


def _build_reset_message(
    msg: PasswordResetEmail, *, from_email: str
) -> EmailMessage:
    em = EmailMessage()
    em["Subject"] = _RESET_SUBJECT
    em["From"] = from_email
    em["To"] = msg.to_email
    em.set_content(
        _RESET_PLAINTEXT.format(
            full_name=msg.to_full_name,
            reset_url=msg.reset_url,
            expires_at=msg.expires_at_iso,
        )
    )
    em.add_alternative(
        _RESET_HTML.format(
            full_name=msg.to_full_name,
            reset_url=msg.reset_url,
            expires_at=msg.expires_at_iso,
        ),
        subtype="html",
    )
    return em


# --- Strategies -------------------------------------------------------------


@dataclass
class StubMailer:
    name: str = "stub"
    sent_invites: list[InviteEmail] = field(default_factory=list)
    sent_resets: list[PasswordResetEmail] = field(default_factory=list)
    sent_demo_registrations: list[DemoRegistrationEmail] = field(default_factory=list)

    def send_invite(self, msg: InviteEmail) -> SendResult:
        self.sent_invites.append(msg)
        logger.info(
            "invite_email_stub_sent",
            extra={"to": msg.to_email, "invite_url": msg.invite_url},
        )
        return SendResult(ok=True)

    def send_password_reset(self, msg: PasswordResetEmail) -> SendResult:
        self.sent_resets.append(msg)
        logger.info(
            "password_reset_email_stub_sent",
            extra={"to": msg.to_email, "reset_url": msg.reset_url},
        )
        return SendResult(ok=True)

    def send_demo_registration(self, msg: DemoRegistrationEmail) -> SendResult:
        self.sent_demo_registrations.append(msg)
        logger.info(
            "demo_registration_email_stub_sent",
            extra={"to": msg.to_email, "confirm_url": msg.confirm_url},
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

    def _send(self, em: EmailMessage, to_email: str, kind: str) -> SendResult:
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
                f"{kind}_email_smtp_failed",
                extra={"to": to_email, "error": str(err)},
            )
            return SendResult(ok=False, error=str(err))

    def send_invite(self, msg: InviteEmail) -> SendResult:
        em = _build_invite_message(msg, from_email=self.from_email or self.username)
        return self._send(em, msg.to_email, kind="invite")

    def send_password_reset(self, msg: PasswordResetEmail) -> SendResult:
        em = _build_reset_message(msg, from_email=self.from_email or self.username)
        return self._send(em, msg.to_email, kind="password_reset")

    def send_demo_registration(self, msg: DemoRegistrationEmail) -> SendResult:
        em = _build_demo_registration_message(
            msg, from_email=self.from_email or self.username
        )
        return self._send(em, msg.to_email, kind="demo_registration")


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


def build_password_reset_url(base_url: str, token: str) -> str:
    return f"{base_url.rstrip('/')}/reset-password?token={token}"


def build_demo_registration_url(base_url: str, token: str) -> str:
    return f"{base_url.rstrip('/')}/register/confirm?token={token}"
