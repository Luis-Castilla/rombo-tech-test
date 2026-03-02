from datetime import date
from typing import Optional
from decimal import Decimal
import logging

from src.application.queries.loan_statement_dto import LoanStatementDTO, InstallmentStatementDTO
from src.domain.ports.output.loan_read_repository import ILoanReadRepository
from src.domain.services.statement_calculator import StatementCalculator

logger = logging.getLogger(__name__)

class GetLoanStatementQuery:
    """
    Query Handler for retrieving the full financial statement of a loan dynamically calculated to today.
    Follows CQRS pattern: strictly distinct from write commands.
    """
    def __init__(self, read_repo: ILoanReadRepository):
        self.read_repo = read_repo
        # We mock Usury Rate here for Default Interest calculations, assume 31.5% EA
        self.usury_rate_mock = Decimal('0.3150') 

    def execute(self, loan_id: str, query_date: Optional[date] = None) -> LoanStatementDTO:
        if not query_date:
            query_date = date.today()
            
        loan = self.read_repo.get_statement_by_loan_id(loan_id)
        if not loan:
            raise ValueError(f"Loan {loan_id} not found.")

        # 1. Base Summaries
        installments = loan.amortization_schedule
        installments_paid = [s for s in installments if s.is_paid]
        
        total_principal_paid = sum(s.principal_payment for s in installments_paid)
        total_interest_paid = sum(s.interest_payment for s in installments_paid)
        
        unpaid = sorted([s for s in installments if not s.is_paid], key=lambda x: x.installment_number)
        current_balance = unpaid[0].principal_balance if unpaid else Decimal('0')

        # 2. Dynamic Metric Calculations
        days_arrears = StatementCalculator.calculate_days_in_arrears(loan, query_date)
        accrued = StatementCalculator.calculate_accrued_interest_pending(loan, query_date)
        default_interest = StatementCalculator.calculate_default_interest(loan, days_arrears, self.usury_rate_mock)
        
        # Current amount due
        total_due = Decimal('0')
        if unpaid:
             # Exact amount to catch up + dynamic interests
             overdue_capital = sum(s.principal_payment for s in unpaid if s.due_date < query_date)
             overdue_interest = sum(s.interest_payment for s in unpaid if s.due_date < query_date)
             total_due = overdue_capital + overdue_interest + accrued + default_interest

        # 3. Construct the View DTO list
        dtos = []
        for s in sorted(installments, key=lambda i: i.installment_number):
            dtos.append(InstallmentStatementDTO(
                installment_number=s.installment_number,
                due_date=s.due_date.isoformat() if hasattr(s.due_date, 'isoformat') else str(s.due_date),
                principal=s.principal_payment,
                interest=s.interest_payment,
                insurance=s.life_insurance,
                others=s.other_charges,
                total=s.total_installment_amount,
                principal_balance=s.principal_balance,
                is_paid=s.is_paid
            ))

        # 4. Construct Final View Model
        statement_view = LoanStatementDTO(
            loan_id=str(loan.id),
            status=loan.status.value,
            requested_amount=loan.requested_amount,
            interest_rate=loan.interest_rate,
            interest_rate_type=loan.interest_rate_type.value,
            term_months=loan.term_months,
            total_principal_paid=total_principal_paid,
            total_interest_paid=total_interest_paid,
            current_principal_balance=current_balance,
            days_in_arrears=days_arrears,
            accrued_interest_pending=accrued,
            default_interest_pending=default_interest,
            total_amount_due_today=total_due,
            installments=dtos
        )

        return statement_view
