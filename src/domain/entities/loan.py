from dataclasses import dataclass, field
from uuid import UUID, uuid4
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from src.domain.entities.enums import (
    InterestRateTypeEnum, PaymentModalityEnum, LoanStatusEnum
)

@dataclass
class AmortizationSchedule:
    loan_id: UUID
    installment_number: int
    due_date: date
    principal_payment: Decimal
    interest_payment: Decimal
    life_insurance: Decimal
    other_charges: Decimal
    total_installment_amount: Decimal
    principal_balance: Decimal
    id: UUID = field(default_factory=uuid4)
    is_paid: bool = False

@dataclass
class Loan:
    customer_id: UUID
    requested_amount: Decimal
    interest_rate: Decimal
    interest_rate_type: InterestRateTypeEnum
    term_months: int
    payment_modality: PaymentModalityEnum
    id: UUID = field(default_factory=uuid4)
    approved_amount: Optional[Decimal] = None
    status: LoanStatusEnum = LoanStatusEnum.SUBMITTED
    application_date: Optional[datetime] = None
    disbursement_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    amortization_schedule: List[AmortizationSchedule] = field(default_factory=list)
