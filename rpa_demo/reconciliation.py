from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable


INVOICE_COLUMNS = {"invoice_id", "po_id", "amount", "currency"}
PURCHASE_ORDER_COLUMNS = {"po_id", "amount", "currency"}
OUTPUT_COLUMNS = [
    "invoice_id",
    "po_id",
    "invoice_amount",
    "invoice_currency",
    "expected_amount",
    "expected_currency",
    "amount_delta",
    "status",
]


def _validate_columns(rows: list[dict[str, str]], required: set[str], label: str) -> None:
    if not rows:
        raise ValueError(f"{label} input cannot be empty")
    missing = sorted(required - set(rows[0]))
    if missing:
        raise ValueError(f"{label} input is missing columns: {', '.join(missing)}")


def _required_value(row: dict[str, str], column: str, label: str) -> str:
    value = row.get(column, "").strip()
    if not value:
        raise ValueError(f"{label} {column} cannot be blank")
    return value


def _amount(value: str, label: str) -> Decimal:
    try:
        parsed = Decimal(value)
    except (InvalidOperation, ValueError) as error:
        raise ValueError(f"{label} amount must be a valid decimal") from error
    if not parsed.is_finite() or parsed <= 0:
        raise ValueError(f"{label} amount must be finite and greater than zero")
    return parsed


def _currency(value: str, label: str) -> str:
    currency = _required_value({"currency": value}, "currency", label).upper()
    if len(currency) != 3 or not currency.isalpha():
        raise ValueError(f"{label} currency must be a three-letter code")
    return currency


def reconcile_records(
    invoices: list[dict[str, str]],
    purchase_orders: list[dict[str, str]],
    tolerance: Decimal = Decimal("0.01"),
) -> tuple[list[dict[str, str]], dict[str, object]]:
    _validate_columns(invoices, INVOICE_COLUMNS, "Invoice")
    _validate_columns(purchase_orders, PURCHASE_ORDER_COLUMNS, "Purchase order")
    if not tolerance.is_finite() or tolerance < 0:
        raise ValueError("tolerance must be finite and non-negative")

    orders: dict[str, tuple[Decimal, str]] = {}
    for row in purchase_orders:
        po_id = _required_value(row, "po_id", "Purchase order")
        if po_id in orders:
            raise ValueError(f"Duplicate purchase-order ID: {po_id}")
        orders[po_id] = (
            _amount(row["amount"], f"Purchase order {po_id}"),
            _currency(row["currency"], f"Purchase order {po_id}"),
        )

    prepared_invoices: list[tuple[str, str, Decimal, str]] = []
    invoice_ids: Counter[str] = Counter()
    for row in invoices:
        invoice_id = _required_value(row, "invoice_id", "Invoice")
        po_id = _required_value(row, "po_id", f"Invoice {invoice_id}")
        amount = _amount(row["amount"], f"Invoice {invoice_id}")
        currency = _currency(row["currency"], f"Invoice {invoice_id}")
        prepared_invoices.append((invoice_id, po_id, amount, currency))
        invoice_ids[invoice_id] += 1

    results: list[dict[str, str]] = []
    for invoice_id, po_id, amount, currency in prepared_invoices:
        expected = orders.get(po_id)
        expected_amount = f"{expected[0]:.2f}" if expected else ""
        expected_currency = expected[1] if expected else ""
        delta = amount - expected[0] if expected else None
        if invoice_ids[invoice_id] > 1:
            status = "duplicate_invoice_id"
        elif expected is None:
            status = "purchase_order_not_found"
        elif currency != expected[1]:
            status = "currency_mismatch"
        elif abs(delta) > tolerance:
            status = "amount_mismatch"
        else:
            status = "matched"
        results.append(
            {
                "invoice_id": invoice_id,
                "po_id": po_id,
                "invoice_amount": f"{amount:.2f}",
                "invoice_currency": currency,
                "expected_amount": expected_amount,
                "expected_currency": expected_currency,
                "amount_delta": f"{delta:.2f}" if delta is not None else "",
                "status": status,
            }
        )

    results.sort(key=lambda row: (row["invoice_id"], row["po_id"]))
    status_counts = dict(sorted(Counter(row["status"] for row in results).items()))
    return results, {"invoice_count": len(results), "status_counts": status_counts}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as source:
        return list(csv.DictReader(source))


def reconcile_files(
    invoice_path: Path,
    purchase_order_path: Path,
    output_dir: Path,
    tolerance: Decimal = Decimal("0.01"),
) -> dict[str, object]:
    results, summary = reconcile_records(
        _read_csv(invoice_path),
        _read_csv(purchase_order_path),
        tolerance,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "reconciliation.csv").open(
        "w", newline="", encoding="utf-8"
    ) as target:
        writer = csv.DictWriter(target, fieldnames=OUTPUT_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(results)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Reconcile invoices against purchase orders without external side effects."
    )
    parser.add_argument(
        "--invoices",
        type=Path,
        default=Path("rpa_demo/sample_data/invoices_to_reconcile.csv"),
    )
    parser.add_argument(
        "--purchase-orders",
        type=Path,
        default=Path("rpa_demo/sample_data/purchase_orders.csv"),
    )
    parser.add_argument("--output-dir", type=Path, default=Path("build/reconciliation"))
    parser.add_argument("--tolerance", type=Decimal, default=Decimal("0.01"))
    args = parser.parse_args(argv)
    summary = reconcile_files(
        args.invoices,
        args.purchase_orders,
        args.output_dir,
        args.tolerance,
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
