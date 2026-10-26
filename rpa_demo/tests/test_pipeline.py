from __future__ import annotations

import csv
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from rpa_demo.pipeline import load_invoices, run_pipeline, select_overdue
from rpa_demo.retry import retry_transient


HEADERS = [
    "invoice_id",
    "customer",
    "due_date",
    "amount",
    "currency",
    "owner_email",
    "status",
]


def write_rows(path: Path, rows: list[list[str]], headers: list[str] = HEADERS) -> None:
    with path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.writer(target)
        writer.writerow(headers)
        writer.writerows(rows)


class PipelineTests(unittest.TestCase):
    def test_transient_retry_succeeds_within_attempt_limit(self) -> None:
        attempts = 0
        waits: list[float] = []

        def operation() -> str:
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise OSError("temporary file lock")
            return "ready"

        result = retry_transient(operation, max_attempts=3, sleeper=waits.append)

        self.assertEqual(result, "ready")
        self.assertEqual(attempts, 3)
        self.assertEqual(waits, [0.5, 0.5])

    def test_permanent_validation_error_is_not_retried(self) -> None:
        attempts = 0

        def operation() -> None:
            nonlocal attempts
            attempts += 1
            raise ValueError("invalid source data")

        with self.assertRaisesRegex(ValueError, "invalid source data"):
            retry_transient(operation, max_attempts=3, sleeper=lambda _: None)
        self.assertEqual(attempts, 1)

    def test_retry_limit_is_enforced(self) -> None:
        attempts = 0

        def operation() -> None:
            nonlocal attempts
            attempts += 1
            raise OSError("source unavailable")

        with self.assertRaisesRegex(OSError, "source unavailable"):
            retry_transient(operation, max_attempts=2, sleeper=lambda _: None)
        self.assertEqual(attempts, 2)

    def test_missing_column_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.csv"
            write_rows(source, [], headers=HEADERS[:-1])

            with self.assertRaisesRegex(ValueError, "status"):
                load_invoices(source)

    def test_duplicate_invoice_id_is_rejected(self) -> None:
        row = [
            "INV-1",
            "Demo Customer",
            "2026-01-01",
            "10.00",
            "USD",
            "owner@example.com",
            "pending",
        ]
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.csv"
            write_rows(source, [row, row])

            with self.assertRaisesRegex(ValueError, "Duplicate invoice_id"):
                load_invoices(source)

    def test_non_finite_amount_is_rejected(self) -> None:
        row = [
            "INV-1",
            "Demo Customer",
            "2026-01-01",
            "NaN",
            "USD",
            "owner@example.com",
            "pending",
        ]
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.csv"
            write_rows(source, [row])

            with self.assertRaisesRegex(ValueError, "amount must be greater than zero"):
                load_invoices(source)

    def test_selection_excludes_closed_and_recent_rows(self) -> None:
        rows = [
            ["OLD", "A", "2026-01-01", "10", "USD", "a@example.com", "pending"],
            ["RECENT", "B", "2026-01-12", "20", "USD", "b@example.com", "pending"],
            ["PAID", "C", "2025-12-01", "30", "USD", "c@example.com", "paid"],
        ]
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.csv"
            write_rows(source, rows)
            invoices = load_invoices(source)

        selected = select_overdue(invoices, date(2026, 1, 15), min_days_overdue=7)
        self.assertEqual([invoice.invoice_id for invoice in selected], ["OLD"])

    def test_run_writes_report_preview_and_audit_event(self) -> None:
        rows = [
            ["INV-2", "B", "2026-01-05", "20", "EUR", "b@example.com", "in_review"],
            ["INV-1", "A", "2025-12-20", "10", "USD", "a@example.com", "pending"],
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "input.csv"
            output = root / "out"
            write_rows(source, rows)

            summary = run_pipeline(source, output, date(2026, 1, 15), 7)

            self.assertEqual(summary.input_rows, 2)
            self.assertEqual(summary.selected_rows, 2)
            self.assertTrue(summary.report_path.exists())
            self.assertIn("INV-1", summary.report_path.read_text(encoding="utf-8"))
            self.assertIn(b"no message was sent", summary.email_preview_path.read_bytes())

            events = summary.audit_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(events), 1)
            event = json.loads(events[0])
            self.assertFalse(event["email_sent"])
            self.assertEqual(event["selected_rows"], 2)


if __name__ == "__main__":
    unittest.main()
