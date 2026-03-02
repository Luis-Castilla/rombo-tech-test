from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID
from src.domain.entities.loan import Loan

class ILoanRepository(ABC):
    @abstractmethod
    def has_active_loans_in_arrears(self, customer_id: UUID) -> bool:
        pass
        
    @abstractmethod
    def save(self, loan: Loan) -> None:
        pass

    @abstractmethod
    def get_by_id_for_update(self, loan_id: UUID) -> Optional[Loan]:
        """Locks the loan row for update to prevent concurrent payment processing."""
        pass

    @abstractmethod
    def payment_exists(self, payment_reference: str) -> bool:
        """Idempotency check."""
        pass

    @abstractmethod
    def save_payment(self, payment: 'Payment') -> None:
        pass
