from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional
import datetime

@dataclass
class InstallmentStatementDTO:
    installment_number: int
    due_date: str
    principal: Decimal
    interest: Decimal
    insurance: Decimal
    others: Decimal
    total: Decimal
    principal_balance: Decimal
    is_paid: bool

@dataclass
class LoanStatementDTO:
    loan_id: str
    status: str
    requested_amount: Decimal
    interest_rate: Decimal
    interest_rate_type: str
    term_months: int
    
    # Financial state at current date
    total_principal_paid: Decimal
    total_interest_paid: Decimal
    current_principal_balance: Decimal
    
    # Dynamic calculations at current date
    days_in_arrears: int
    accrued_interest_pending: Decimal
    default_interest_pending: Decimal
    total_amount_due_today: Decimal
    
    # Historic and pending
    installments: List[InstallmentStatementDTO]
