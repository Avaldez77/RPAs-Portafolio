from __future__ import annotations

import csv
import json
import os
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from email.message import EmailMessage
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterable

from .models import Invoice


REQUIRED_COLUMNS = (
    "invoice_id",
    "customer",
    "due_date",
    "amount",
    "currency",
    "owner_email",
    "status",
)
ALLOWED_STATUSES = {"pending", "in_review", "paid", "cancelled"}
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True, slots=True)
class RunSummary:
    input_rows: int
    selected_rows: int
    report_path: Path
    email_preview_path: Path
    audit_path: Path


def _required(value: str | None, field: str, row_number: int) -> str:
    cleaned = (value or "").strip()
    if not cleaned:
        raise ValueError(f"Row {row_number}: '{field}' is required")
    return cleaned


def _parse_invoice(row: dict[str, str], row_number: int) -> Invoice:
    invoice_id = _required(row.get("invoice_id"), "invoice_id", row_number)
    customer = _required(row.get("customer"), "customer", row_number)

    due_date_text = _required(row.get("due_date"), "due_date", row_number)
    try:
        due_date = date.fromisoformat(due_date_text)
    except ValueError as exc:
        raise ValueError(
            f"Row {row_number}: due_date must use YYYY-MM-DD"
        ) from exc

    amount_text = _required(row.get("amount"), "amount", row_number)
    try:
        amount = Decimal(amount_text)
    except InvalidOperation as exc:
        raise ValueError(f"Row {row_number}: amount is not a decimal") from exc
    if not amount.is_finite() or amount <= 0:
        raise ValueError(f"Row {row_number}: amount must be greater than zero")

    currency = _required(row.get("currency"), "currency", row_number).upper()
    if len(currency) != 3 or not currency.isalpha():
        raise ValueError(f"Row {row_number}: currency must contain three letters")

    owner_email = _required(row.get("owner_email"), "owner_email", row_number).lower()
    if not EMAIL_PATTERN.fullmatch(owner_email):
        raise ValueError(f"Row {row_number}: owner_email is invalid")

    status = _required(row.get("status"), "status", row_number).lower()
    if status not in ALLOWED_STATUSES:
        allowed = ", ".join(sorted(ALLOWED_STATUSES))
        raise ValueError(f"Row {row_number}: status must be one of {allowed}")

    return Invoice(
        invoice_id=invoice_id,
        customer=customer,
        due_date=due_date,
        amount=amount,
        currency=currency,
        owner_email=owner_email,
        status=status,
    )


def load_invoices(path: Path) -> list[Invoice]:
    with path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None:
            raise ValueError("Input file does not contain a header")

        missing = [name for name in REQUIRED_COLUMNS if name not in reader.fieldnames]
        if missing:
            raise ValueError(f"Input is missing columns: {', '.join(missing)}")

        invoices = [_parse_invoice(row, index) for index, row in enumerate(reader, start=2)]

    seen: set[str] = set()
    duplicates: set[str] = set()
    for invoice in invoices:
        if invoice.invoice_id in seen:
            duplicates.add(invoice.invoice_id)
        seen.add(invoice.invoice_id)
    if duplicates:
        raise ValueError(f"Duplicate invoice_id values: {', '.join(sorted(duplicates))}")

    return invoices


def select_overdue(
    invoices: Iterable[Invoice], as_of: date, min_days_overdue: int
) -> list[Invoice]:
    if min_days_overdue < 0:
        raise ValueError("min_days_overdue cannot be negative")

    selected = [
        invoice
        for invoice in invoices
        if invoice.status in {"pending", "in_review"}
        and invoice.days_overdue(as_of) >= min_days_overdue
    ]
    return sorted(
        selected,
        key=lambda invoice: (-invoice.days_overdue(as_of), invoice.invoice_id),
    )


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="",
        dir=path.parent,
        delete=False,
    ) as temporary:
        temporary.write(text)
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, path)


def write_report(invoices: Iterable[Invoice], as_of: date, path: Path) -> None:
    rows = list(invoices)
    from io import StringIO

    buffer = StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(
        [
            "invoice_id",
            "customer",
            "due_date",
            "days_overdue",
            "amount",
            "currency",
            "owner_email",
            "status",
        ]
    )
    for invoice in rows:
        writer.writerow(
            [
                invoice.invoice_id,
                invoice.customer,
                invoice.due_date.isoformat(),
                invoice.days_overdue(as_of),
                format(invoice.amount, "f"),
                invoice.currency,
                invoice.owner_email,
                invoice.status,
            ]
        )
    _atomic_write_text(path, buffer.getvalue())


def write_email_preview(
    invoices: Iterable[Invoice], as_of: date, report_path: Path, path: Path
) -> None:
    rows = list(invoices)
    recipients = sorted({invoice.owner_email for invoice in rows})
    totals: dict[str, Decimal] = {}
    for invoice in rows:
        totals[invoice.currency] = totals.get(invoice.currency, Decimal("0")) + invoice.amount

    totals_text = ", ".join(
        f"{currency} {amount:,.2f}" for currency, amount in sorted(totals.items())
    ) or "no outstanding amount"

    message = EmailMessage()
    message["Subject"] = f"Invoice follow-up preview | {as_of.isoformat()}"
    message["From"] = "rpa-demo@example.com"
    message["To"] = ", ".join(recipients) if recipients else "operations@example.com"
    message.set_content(
        "This is a local preview; no message was sent.\n\n"
        f"Invoices requiring follow-up: {len(rows)}\n"
        f"Outstanding totals: {totals_text}\n"
        f"As-of date: {as_of.isoformat()}\n"
    )
    message.add_attachment(
        report_path.read_bytes(),
        maintype="text",
        subtype="csv",
        filename=report_path.name,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(message.as_bytes())


def append_audit_event(summary: RunSummary, as_of: date, min_days_overdue: int) -> None:
    event = {
        "event": "invoice_follow_up_completed",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "as_of": as_of.isoformat(),
        "min_days_overdue": min_days_overdue,
        "input_rows": summary.input_rows,
        "selected_rows": summary.selected_rows,
        "report": summary.report_path.name,
        "email_sent": False,
    }
    summary.audit_path.parent.mkdir(parents=True, exist_ok=True)
    with summary.audit_path.open("a", encoding="utf-8") as audit_file:
        audit_file.write(json.dumps(event, sort_keys=True) + "\n")


def run_pipeline(
    input_path: Path,
    output_dir: Path,
    as_of: date,
    min_days_overdue: int = 0,
) -> RunSummary:
    invoices = load_invoices(input_path)
    selected = select_overdue(invoices, as_of, min_days_overdue)

    report_path = output_dir / "pending_invoices.csv"
    email_preview_path = output_dir / "notification_preview.eml"
    audit_path = output_dir / "audit.jsonl"

    write_report(selected, as_of, report_path)
    write_email_preview(selected, as_of, report_path, email_preview_path)

    summary = RunSummary(
        input_rows=len(invoices),
        selected_rows=len(selected),
        report_path=report_path,
        email_preview_path=email_preview_path,
        audit_path=audit_path,
    )
    append_audit_event(summary, as_of, min_days_overdue)
    return summary
