from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from .pipeline import run_pipeline


PACKAGE_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = PACKAGE_DIR.parent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a local invoice follow-up report from synthetic CSV data."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=PACKAGE_DIR / "sample_data" / "pending_invoices.csv",
        help="Source CSV file.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPOSITORY_ROOT / "build" / "demo-run",
        help="Directory for the report, email preview, and audit log.",
    )
    parser.add_argument(
        "--as-of",
        type=date.fromisoformat,
        default=date.today(),
        help="Reference date in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--min-days-overdue",
        type=int,
        default=0,
        help="Minimum number of overdue days required for selection.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summary = run_pipeline(
            input_path=args.input,
            output_dir=args.output_dir,
            as_of=args.as_of,
            min_days_overdue=args.min_days_overdue,
        )
    except (OSError, ValueError) as exc:
        print(f"Run failed: {exc}")
        return 2

    print(
        f"Processed {summary.input_rows} rows; "
        f"selected {summary.selected_rows} for follow-up."
    )
    print(f"Report: {summary.report_path}")
    print(f"Email preview: {summary.email_preview_path}")
    print(f"Audit log: {summary.audit_path}")
    return 0
