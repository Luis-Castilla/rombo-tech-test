from abc import ABC, abstractmethod
from typing import Optional
from src.application.queries.loan_statement_dto import LoanStatementDTO

class ILoanReadRepository(ABC):
    """
    Port (Interface) for CQRS Read side. 
    Returns DTOs perfectly shaped for the view, hiding domain logic from persistence optimization.
    """
    
    @abstractmethod
    def get_statement_by_loan_id(self, loan_id: str) -> Optional['Loan']:
        """
        Loads the Loan with its whole schedule graph using optimized SQL querying (e.g., joinedload).
        Returns the Domain Entity to be passed through the calculator.
        """
        pass
