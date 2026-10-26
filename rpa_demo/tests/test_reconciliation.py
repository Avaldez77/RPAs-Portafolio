from __future__ import annotations

import csv
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from rpa_demo.reconciliation import reconcile_files, reconcile_records


class ReconciliationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.orders = [
            {"po_id": "PO-1", "amount": "100.00", "currency": "USD"},
            {"po_id": "PO-2", "amount": "50.00", "currency": "EUR"},
        ]

    def test_matches_and_exposes_exceptions(self) -> None:
        invoices = [
            {"invoice_id": "I-1", "po_id": "PO-1", "amount": "100.01", "currency": "usd"},
            {"invoice_id": "I-2", "po_id": "PO-2", "amount": "60", "currency": "EUR"},
            {"invoice_id": "I-3", "po_id": "PO-2", "amount": "50", "currency": "USD"},
            {"invoice_id": "I-4", "po_id": "PO-X", "amount": "20", "currency": "USD"},
        ]

        results, summary = reconcile_records(invoices, self.orders)

        self.assertEqual(
            [row["status"] for row in results],
            [
                "matched",
                "amount_mismatch",
                "currency_mismatch",
                "purchase_order_not_found",
            ],
        )
        self.assertEqual(summary["invoice_count"], 4)

    def test_duplicate_invoice_ids_are_not_silently_dropped(self) -> None:
        invoices = [
            {"invoice_id": "I-1", "po_id": "PO-1", "amount": "100", "currency": "USD"},
            {"invoice_id": "I-1", "po_id": "PO-1", "amount": "100", "currency": "USD"},
        ]

        results, summary = reconcile_records(invoices, self.orders)

        self.assertEqual(len(results), 2)
        self.assertEqual([row["status"] for row in results], ["duplicate_invoice_id"] * 2)
        self.assertEqual(summary["status_counts"], {"duplicate_invoice_id": 2})

    def test_rejects_invalid_amount_and_duplicate_purchase_orders(self) -> None:
        invalid_invoice = [
            {"invoice_id": "I-1", "po_id": "PO-1", "amount": "NaN", "currency": "USD"}
        ]
        with self.assertRaisesRegex(ValueError, "finite and greater than zero"):
            reconcile_records(invalid_invoice, self.orders)

        duplicate_orders = self.orders + [self.orders[0]]
        with self.assertRaisesRegex(ValueError, "Duplicate purchase-order ID"):
            reconcile_records(
                [{"invoice_id": "I-1", "po_id": "PO-1", "amount": "100", "currency": "USD"}],
                duplicate_orders,
            )

    def test_files_are_repeatable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            invoice_path = root / "invoices.csv"
            po_path = root / "orders.csv"
            output_dir = root / "output"
            with invoice_path.open("w", newline="", encoding="utf-8") as target:
                writer = csv.DictWriter(
                    target, fieldnames=["invoice_id", "po_id", "amount", "currency"]
                )
                writer.writeheader()
                writer.writerow(
                    {"invoice_id": "I-1", "po_id": "PO-1", "amount": "100", "currency": "USD"}
                )
            with po_path.open("w", newline="", encoding="utf-8") as target:
                writer = csv.DictWriter(
                    target, fieldnames=["po_id", "amount", "currency"]
                )
                writer.writeheader()
                writer.writerows(self.orders)

            first = reconcile_files(invoice_path, po_path, output_dir, Decimal("0.01"))
            report_bytes = (output_dir / "reconciliation.csv").read_bytes()
            second = reconcile_files(invoice_path, po_path, output_dir, Decimal("0.01"))

            self.assertEqual(first, second)
            self.assertEqual(report_bytes, (output_dir / "reconciliation.csv").read_bytes())


if __name__ == "__main__":
    unittest.main()
