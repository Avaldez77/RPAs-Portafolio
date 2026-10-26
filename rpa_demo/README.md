# Invoice follow-up demo

This small project mirrors a common RPA hand-off: validate an export, identify
overdue records, build a report, prepare a notification, and leave an audit
trail. It uses fictional invoices and stops before sending an email.

## What the run produces

- `pending_invoices.csv`: filtered records sorted by urgency.
- `notification_preview.eml`: an email that can be inspected in a mail client.
- `audit.jsonl`: one structured event for the run.

No SAP, SMTP, Outlook, or Excel installation is required.

## Example

From the repository root:

```bash
python -m rpa_demo --as-of 2026-01-15 --min-days-overdue 7
```

The defaults read `rpa_demo/sample_data/pending_invoices.csv` and write to
`build/demo-run`.

## Input contract

The CSV must include these columns:

| Column | Rule |
| --- | --- |
| `invoice_id` | Required and unique |
| `customer` | Required |
| `due_date` | ISO date (`YYYY-MM-DD`) |
| `amount` | Positive decimal value |
| `currency` | Three-letter currency code |
| `owner_email` | Basic email format validation |
| `status` | `pending`, `in_review`, `paid`, or `cancelled` |

Rows marked `paid` or `cancelled` never appear in the report. The overdue
threshold is inclusive: `--min-days-overdue 7` includes a record once it is at
least seven days late.

## Tests

```bash
python -m unittest discover -s rpa_demo/tests -v
```

The tests cover schema validation, duplicate detection, filtering, deterministic
ordering, and generation of the three output artifacts.
