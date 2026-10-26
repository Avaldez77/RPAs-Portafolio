# RPA engineering exercises

All exercises use the invoice follow-up demo and synthetic data. Do not connect
the exercises to SAP, Outlook, SMTP, or a production environment.

## 1. Idempotent report generation

Run the same input twice with the same as-of date. Add a stable run identifier
and define how repeated runs should behave without duplicating audit events or
overwriting evidence unexpectedly.

**Acceptance criteria:** identical inputs produce identical report bytes; the
chosen audit behavior is documented and tested.

## 2. Retry and recovery policy

Add a bounded retry policy around a simulated transient file-read failure.
Inject the failure in a test rather than relying on an actual network share.

**Acceptance criteria:** attempts are capped, permanent validation errors are
not retried, and the final failure is visible to the caller.

## 3. Notification approval gate

Extend the local email preview with a dry-run manifest and an explicit
approval state. Keep sending disabled in tests and require a separate,
reviewed configuration before any external integration.

**Acceptance criteria:** preview generation never sends email, recipients are
validated before approval, and tests prove both approved and rejected paths.

## 4. Failure-path coverage

Add tests for malformed dates, non-finite amounts, empty input, and output
write failures. Confirm that no success-shaped output is reported after a
failed run.

Run the current tests from the repository root:

```bash
python -m unittest discover -s rpa_demo/tests -v
```
