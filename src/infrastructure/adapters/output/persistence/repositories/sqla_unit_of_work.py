from src.domain.ports.output.unit_of_work import IUnitOfWork
from src.infrastructure.adapters.output.persistence.repositories.sqla_customer_repository import SqlAlchemyCustomerRepository
from src.infrastructure.adapters.output.persistence.repositories.sqla_loan_repository import SqlAlchemyLoanRepository
from src.infrastructure.adapters.output.persistence.repositories.sqla_accounting_repository import SqlAlchemyAccountingRepository

class SqlAlchemyUnitOfWork(IUnitOfWork):
    def __init__(self, session):
        self.session = session
        self.customers = SqlAlchemyCustomerRepository(self.session)
        self.loans = SqlAlchemyLoanRepository(self.session)
        self.accounting = SqlAlchemyAccountingRepository(self.session)

    def __enter__(self):
        # SQLAlchemy session already started automatically by Flask-SQLAlchemy or explicitly
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            # We enforce explicit commit in the use case. 
            pass

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()
