from __future__ import annotations

import os
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path


@dataclass
class SmtpConfig:
    host: str
    port: int
    username: str
    password: str
    sender: str
    use_ssl: bool = False
    use_starttls: bool = True

    @classmethod
    def from_sources(
        cls,
        *,
        host: str | None = None,
        port: int | None = None,
        username: str | None = None,
        password: str | None = None,
        sender: str | None = None,
        use_ssl: bool = False,
        use_starttls: bool = True,
    ) -> "SmtpConfig":
        resolved_host = host or os.environ.get("SMTP_HOST", "").strip()
        resolved_port = port or int(os.environ.get("SMTP_PORT", "587"))
        resolved_username = username or os.environ.get("SMTP_USERNAME", "").strip()
        resolved_password = password or os.environ.get("SMTP_PASSWORD", "").strip()
        resolved_sender = sender or os.environ.get("SENDER_EMAIL", "").strip()

        return cls(
            host=resolved_host,
            port=resolved_port,
            username=resolved_username,
            password=resolved_password,
            sender=resolved_sender,
            use_ssl=use_ssl,
            use_starttls=use_starttls,
        )

    def validate(self) -> None:
        missing_fields: list[str] = []

        if not self.host:
            missing_fields.append("smtp host")
        if not self.port:
            missing_fields.append("smtp port")
        if not self.username:
            missing_fields.append("smtp username")
        if not self.password:
            missing_fields.append("smtp password")
        if not self.sender:
            missing_fields.append("sender email")

        if missing_fields:
            missing = ", ".join(missing_fields)
            raise ValueError(
                "Faltan datos SMTP para enviar al Kindle: "
                f"{missing}. Usa argumentos CLI o variables de entorno SMTP_* y SENDER_EMAIL."
            )

        if self.use_ssl and self.use_starttls:
            raise ValueError("No se puede usar SSL y STARTTLS al mismo tiempo.")


def resolve_kindle_recipient(cli_value: str | None = None) -> str:
    recipient = (cli_value or os.environ.get("RECIPIENT_EMAIL", "")).strip()
    if not recipient:
        raise ValueError(
            "No se definio el correo Kindle. Usa --kindle-email o la variable RECIPIENT_EMAIL."
        )
    return recipient


def send_epub_via_email(
    *,
    epub_file: Path,
    recipient_email: str,
    smtp_config: SmtpConfig,
    subject: str | None = None,
    body: str | None = None,
) -> None:
    if not epub_file.is_file():
        raise FileNotFoundError(f"No existe el archivo EPUB para envio: {epub_file}")

    smtp_config.validate()

    message = EmailMessage()
    message["From"] = smtp_config.sender
    message["To"] = recipient_email
    message["Subject"] = subject or f"Send to Kindle: {epub_file.stem}"
    message.set_content(
        body
        or (
            "Archivo EPUB adjunto para enviar a Kindle.\n\n"
            "Asegurate de haber autorizado el remitente en tu cuenta de Amazon."
        )
    )

    with epub_file.open("rb") as epub_stream:
        message.add_attachment(
            epub_stream.read(),
            maintype="application",
            subtype="epub+zip",
            filename=epub_file.name,
        )

    if smtp_config.use_ssl:
        with smtplib.SMTP_SSL(smtp_config.host, smtp_config.port) as server:
            server.login(smtp_config.username, smtp_config.password)
            server.send_message(message)
        return

    with smtplib.SMTP(smtp_config.host, smtp_config.port) as server:
        server.ehlo()
        if smtp_config.use_starttls:
            server.starttls()
            server.ehlo()
        server.login(smtp_config.username, smtp_config.password)
        server.send_message(message)
