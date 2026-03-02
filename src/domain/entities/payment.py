from dataclasses import dataclass, field
from uuid import UUID, uuid4
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from src.domain.entities.enums import PaymentMethodEnum

@dataclass
class PaymentAllocation:
    payment_id: UUID
    legal_fees_amount: Decimal
    insurance_amount: Decimal
    default_interest_amount: Decimal
    ordinary_interest_amount: Decimal
    principal_amount: Decimal
    id: UUID = field(default_factory=uuid4)
    amortization_schedule_id: Optional[UUID] = None

@dataclass
class Payment:
    loan_id: UUID
    paid_amount: Decimal
    payment_reference: str
    payment_method: PaymentMethodEnum
    id: UUID = field(default_factory=uuid4)
    payment_date: Optional[datetime] = None
    allocations: List[PaymentAllocation] = field(default_factory=list)
