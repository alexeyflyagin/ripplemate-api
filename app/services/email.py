import logging
import sys
from abc import ABC, abstractmethod

logger = logging.getLogger("app.email")
if not logger.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s: %(message)s"))
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


class EmailSender(ABC):
    @abstractmethod
    async def send(self, to: str, subject: str, body: str) -> None: ...


class ConsoleEmailSender(EmailSender):
    async def send(self, to: str, subject: str, body: str) -> None:
        logger.info(
            "EMAIL SENT\n  to:      %s\n  subject: %s\n  body:\n%s",
            to,
            subject,
            body,
        )


# TODO: add ResendEmailSender(EmailSender) and return it here in production.


def get_email_sender() -> EmailSender:
    return ConsoleEmailSender()
