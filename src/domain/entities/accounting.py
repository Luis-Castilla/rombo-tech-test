from dataclasses import dataclass, field
from uuid import UUID, uuid4
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from src.domain.entities.enums import AccountNatureEnum

@dataclass
class ChartOfAccount:
    code: str
    name: str
    nature: AccountNatureEnum

@dataclass
class JournalEntryLine:
    journal_entry_id: UUID
    account_code: str
    debit: Decimal
    credit: Decimal
    id: UUID = field(default_factory=uuid4)

@dataclass
class JournalEntry:
    description: str
    id: UUID = field(default_factory=uuid4)
    entry_date: Optional[datetime] = None
    operation_reference: Optional[UUID] = None
    lines: List[JournalEntryLine] = field(default_factory=list)
