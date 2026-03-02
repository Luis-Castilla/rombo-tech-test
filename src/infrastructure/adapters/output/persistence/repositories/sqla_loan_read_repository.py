from decimal import Decimal
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import joinedload
from src.domain.ports.output.loan_read_repository import ILoanReadRepository
from src.infrastructure.adapters.output.persistence.models import LoanModel
from src.domain.entities.loan import Loan, AmortizationSchedule

class SqlAlchemyLoanReadRepository(ILoanReadRepository):
    def __init__(self, session):
        self.session = session

    def get_statement_by_loan_id(self, loan_id: str) -> Optional[Loan]:
        """
        Loads the Loan with schedules eagerly to map to the view DTO.
        Crucial requirement: Avoid N+1 queries using joinedload().
        """
        
        try:
            loan_uuid = UUID(loan_id)
        except ValueError:
            return None
            
        # 1. Single database query fetching Loan joined with Amortization Schedules
        model = self.session.query(LoanModel)\
            .options(joinedload(LoanModel.amortization_schedules))\
            .filter_by(id=loan_uuid).first()
            
        if not model:
            return None
            
        # 2. Map to Domain Entity needed for Calculator
        loan = Loan(
            id=model.id,
            customer_id=model.customer_id,
            requested_amount=model.requested_amount,
            approved_amount=model.approved_amount,
            interest_rate=model.interest_rate,
            interest_rate_type=model.interest_rate_type,
            term_months=model.term_months,
            payment_modality=model.payment_modality,
            status=model.status,
            application_date=model.application_date,
            disbursement_date=model.disbursement_date
        )
        
        schedule_entities = []
        for sched_model in model.amortization_schedules:
            schedule_entities.append(AmortizationSchedule(
                id=sched_model.id,
                loan_id=sched_model.loan_id,
                installment_number=sched_model.installment_number,
                due_date=sched_model.due_date,
                principal_payment=sched_model.principal_payment,
                interest_payment=sched_model.interest_payment,
                life_insurance=sched_model.life_insurance,
                other_charges=sched_model.other_charges,
                total_installment_amount=sched_model.total_installment_amount,
                principal_balance=sched_model.principal_balance,
                is_paid=sched_model.is_paid
            ))
            
        loan.amortization_schedule = schedule_entities
        
        return loan
