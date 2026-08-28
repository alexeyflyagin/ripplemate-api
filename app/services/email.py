from abc import ABC, abstractmethod


class EmailSender(ABC):
    @abstractmethod
    async def send(self, to: str, subject: str, body: str) -> None: ...


class ConsoleEmailSender(EmailSender):
    async def send(self, to: str, subject: str, body: str) -> None:
        print("=" * 60)
        print(f"[EMAIL] to:      {to}")
        print(f"[EMAIL] subject: {subject}")
        print(f"[EMAIL] body:\n{body}")
        print("=" * 60, flush=True)


# TODO: add ResendEmailSender(EmailSender) and return it here in production.


def get_email_sender() -> EmailSender:
    return ConsoleEmailSender()
