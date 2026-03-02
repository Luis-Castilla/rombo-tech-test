from abc import ABC, abstractmethod
from src.domain.ports.output.customer_repository import ICustomerRepository
from src.domain.ports.output.loan_repository import ILoanRepository
from src.domain.ports.output.accounting_repository import IAccountingRepository

class IUnitOfWork(ABC):
    customers: ICustomerRepository
    loans: ILoanRepository
    accounting: IAccountingRepository

    @abstractmethod
    def __enter__(self):
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    def commit(self):
        pass

    @abstractmethod
    def rollback(self):
        pass
