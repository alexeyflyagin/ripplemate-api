import logging
import sys
from abc import ABC, abstractmethod

import resend

from app.core.config import settings

logger = logging.getLogger("app.email")
if not logger.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s: %(message)s"))
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


class EmailSender(ABC):
    @abstractmethod
    async def send(
        self, to: str, subject: str, text: str, html: str | None = None
    ) -> None: ...


class ConsoleEmailSender(EmailSender):
    async def send(
        self, to: str, subject: str, text: str, html: str | None = None
    ) -> None:
        logger.info(
            "EMAIL SENT\n  to:      %s\n  subject: %s\n  text:\n%s",
            to,
            subject,
            text,
        )


class ResendEmailSender(EmailSender):
    def __init__(self, api_key: str) -> None:
        resend.api_key = api_key

    async def send(
        self, to: str, subject: str, text: str, html: str | None = None
    ) -> None:
        payload = {
            "from": settings.resend_from_email,
            "to": to,
            "subject": subject,
            "text": text,
        }
        if html:
            payload["html"] = html
        try:
            await resend.Emails.send_async(payload)
        except Exception:
            logger.exception("Failed to send email to %s", to)


def get_email_sender() -> EmailSender:
    if settings.resend_api_key:
        return ResendEmailSender(settings.resend_api_key)
    return ConsoleEmailSender()
