from dataclasses import dataclass, field
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional
from src.domain.entities.enums import DocumentTypeEnum, PortfolioRiskEnum
from decimal import Decimal
from decimal import Decimal

MINIMUM_ELIGIBLE_CREDIT_SCORE = 600

@dataclass
class Customer:
    document_type: DocumentTypeEnum
    document_number: str
    first_name: str
    last_name: str
    city: str
    id: UUID = field(default_factory=uuid4)
    email: Optional[str] = None
    phone_number: Optional[str] = None
    credit_score: Optional[int] = None
    borrowing_capacity: Decimal = Decimal('0.00')
    risk_classification: PortfolioRiskEnum = PortfolioRiskEnum.A
    created_at: Optional[datetime] = None

    def meets_eligibility_criteria(self, requested_amount: Decimal, has_arrears: bool) -> bool:
        """
        Validates if the customer is eligible for a new loan based on:
        1. Credit score must be strictly greater than 600.
        2. Cannot have any existing loan in IN_ARREARS state.
        3. Requested amount cannot exceed the borrowing capacity.
        """
        if self.credit_score is None or self.credit_score <= MINIMUM_ELIGIBLE_CREDIT_SCORE:
            return False
        
        if has_arrears:
            return False
            
        if requested_amount > self.borrowing_capacity:
            return False
            
        return True
