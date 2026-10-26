"""Build and optionally send dashboard emails described by a JSON manifest.

The portfolio version defaults to preview mode. Use ``--send`` only after the
SMTP settings and recipient manifest have been reviewed in the target
environment.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import make_msgid
from pathlib import Path


DEFAULT_BODY = (
    "Hello,\n\n"
    "Please find the latest dashboard snapshot attached and embedded below.\n\n"
    "Regards,\nAutomation team"
)


def load_manifest(path: Path) -> list[dict[str, object]]:
    with path.open(encoding="utf-8") as source:
        payload = json.load(source)
    if not isinstance(payload, list):
        raise ValueError("The recipient manifest must contain a JSON list")
    return payload


def clean_recipients(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    recipients = [str(item).strip() for item in value if str(item).strip()]
    return sorted(set(recipients))


def build_message(image_path: Path, recipients: list[str], from_address: str) -> EmailMessage:
    if not recipients:
        raise ValueError(f"No recipients configured for {image_path}")
    if not image_path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")

    mime_type, _ = mimetypes.guess_type(image_path.name)
    if mime_type != "image/png":
        raise ValueError(f"Only PNG dashboard images are supported: {image_path.name}")

    image_bytes = image_path.read_bytes()
    content_id = make_msgid(domain="rpa-preview.local")
    message = EmailMessage()
    message["Subject"] = f"Weekly dashboard | {image_path.stem.replace('_', ' ').title()}"
    message["From"] = from_address
    message["To"] = ", ".join(recipients)
    message.set_content(DEFAULT_BODY)
    message.add_alternative(
        "<p>Hello,</p>"
        "<p>Please find the latest dashboard snapshot attached and embedded below.</p>"
        f'<p><img src="cid:{content_id[1:-1]}" alt="Dashboard snapshot"></p>'
        "<p>Regards,<br>Automation team</p>",
        subtype="html",
    )

    html_part = message.get_payload()[-1]
    html_part.add_related(
        image_bytes,
        maintype="image",
        subtype="png",
        cid=content_id,
        filename=image_path.name,
        disposition="inline",
    )
    message.add_attachment(
        image_bytes,
        maintype="image",
        subtype="png",
        filename=image_path.name,
    )
    return message


def save_preview(message: EmailMessage, preview_dir: Path, image_path: Path) -> Path:
    preview_dir.mkdir(parents=True, exist_ok=True)
    destination = preview_dir / f"{image_path.stem}.eml"
    destination.write_bytes(message.as_bytes())
    return destination


def smtp_password() -> str:
    password = os.getenv("RPA_SMTP_PASSWORD", "").strip()
    if password:
        return password

    secret_path = os.getenv("RPA_SMTP_PASSWORD_FILE", "").strip()
    if secret_path:
        return Path(secret_path).read_text(encoding="utf-8").strip()
    raise RuntimeError(
        "Set RPA_SMTP_PASSWORD or RPA_SMTP_PASSWORD_FILE before using --send"
    )


def send_messages(
    messages: list[EmailMessage], host: str, port: int, username: str, use_starttls: bool
) -> None:
    context = ssl.create_default_context()
    with smtplib.SMTP(host, port, timeout=30) as smtp:
        smtp.ehlo()
        if use_starttls:
            smtp.starttls(context=context)
            smtp.ehlo()
        if username:
            smtp.login(username, smtp_password())
        for message in messages:
            smtp.send_message(message)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(os.getenv("RPA_RECIPIENTS_JSON", "recipients.example.json")),
    )
    parser.add_argument("--preview-dir", type=Path, default=Path("email-previews"))
    parser.add_argument("--send", action="store_true", help="Send after previews are created")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    from_address = os.getenv("RPA_FROM_ADDRESS", "rpa-bot@example.com")

    messages: list[EmailMessage] = []
    skipped = 0
    for index, entry in enumerate(load_manifest(args.manifest), start=1):
        if not isinstance(entry, dict):
            print(f"[WARN] Entry {index} is not an object; skipped")
            skipped += 1
            continue

        image_path = Path(str(entry.get("file_path", "")))
        recipients = clean_recipients(entry.get("emails"))
        try:
            message = build_message(image_path, recipients, from_address)
        except (FileNotFoundError, ValueError) as exc:
            print(f"[WARN] {exc}; skipped")
            skipped += 1
            continue

        preview_path = save_preview(message, args.preview_dir, image_path)
        print(f"[OK] Preview written: {preview_path}")
        messages.append(message)

    if args.send and messages:
        host = os.getenv("RPA_SMTP_HOST", "").strip()
        if not host:
            raise RuntimeError("Set RPA_SMTP_HOST before using --send")
        port = int(os.getenv("RPA_SMTP_PORT", "587"))
        username = os.getenv("RPA_SMTP_USERNAME", "").strip()
        use_starttls = os.getenv("RPA_SMTP_STARTTLS", "true").lower() != "false"
        send_messages(messages, host, port, username, use_starttls)
        print(f"[OK] Sent {len(messages)} message(s)")
    elif messages:
        print(f"[DRY RUN] Built {len(messages)} message(s); nothing was sent")

    print(f"Completed with {skipped} skipped manifest entr{'y' if skipped == 1 else 'ies'}")
    return 0 if messages else 1


if __name__ == "__main__":
    raise SystemExit(main())
