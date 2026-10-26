from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Invoice:
    invoice_id: str
    customer: str
    due_date: date
    amount: Decimal
    currency: str
    owner_email: str
    status: str

    def days_overdue(self, as_of: date) -> int:
        return (as_of - self.due_date).days
