# RPA & Process Automation Portfolio

This repository is a collection of sanitized automation case studies built around
reporting, order management, invoice follow-up, and SAP-related workflows. The
production integrations depend on private enterprise systems, so host names,
credentials, recipients, and business data have been removed or replaced with
placeholders.

The repository has two kinds of material:

- **Case studies** document the original process, design decisions, and selected
  implementation excerpts.
- **Runnable demos** reproduce the same engineering patterns with synthetic data
  and no connection to a company system.

## Projects

| Project | Focus | Code in this repository |
| --- | --- | --- |
| [SAP Parallel Automation Flow](./SAP%20Parallel%20Automation%20Flow/) | Concurrent Playwright sessions, isolated downloads, Outlook hand-off | Sanitized implementation |
| [Pending invoices](./Pending%20invoices/) | Filtering, file handling, notification branches | Sanitized workflow scripts |
| [Reassignation](./Reassignation/) | Input preparation and SAP re-allocation support | Sanitized workflow scripts |
| [Unassign](./Unassign/) | Data consolidation and de-allocation support | Sanitized workflow scripts |
| [Back Orders](./Back%20Orders/) | Excel processing and Tableau Hyper output | Sanitized workflow scripts |
| [Send automatic report](./Send%20automatic%20report/) | Dashboard capture and email distribution | Sanitized implementation |
| [Invoice follow-up demo](./rpa_demo/) | Reproducible validation, reporting, email preview, and audit log | Fully runnable demo |
| [Hands-on exercises](./Exercises/README.md) | Idempotency, retries, and failure-path validation without live integrations | Exercise guide |

## Run the local demo

The demo uses only the Python standard library and never sends email. It creates
a CSV report, an `.eml` preview, and a JSON Lines audit log.

```bash
python -m rpa_demo \
  --input rpa_demo/sample_data/pending_invoices.csv \
  --output-dir build/demo-run \
  --as-of 2026-01-15 \
  --min-days-overdue 7
```

Run the automated checks with:

```bash
python -m unittest discover -s rpa_demo/tests -v
```

## Design principles

- Configuration and secrets stay outside the code.
- External side effects are disabled in examples unless they are explicitly
  requested.
- Inputs are validated before a browser, spreadsheet, or email client is opened.
- Output files are deterministic and safe to regenerate.
- Logs record what happened without exposing customer data or credentials.
- The portfolio demo is intentionally dry-run only; production integrations
  require a separately reviewed deployment and operational controls.

## Portfolio note

Company-specific details are intentionally omitted. The included sample records
are fictional and exist only to make the workflow reviewable and testable.
