import pytest
import datetime
from decimal import Decimal
from freezegun import freeze_time
from uuid import uuid4

from src.domain.entities.loan import Loan, AmortizationSchedule, LoanStatusEnum
from src.domain.entities.enums import InterestRateTypeEnum, PaymentModalityEnum
from src.domain.services.statement_calculator import StatementCalculator

@pytest.fixture
def mock_loan():
    loan = Loan(
        id=uuid4(), customer_id=uuid4(), requested_amount=Decimal('1000'), 
        interest_rate=Decimal('0.02'), interest_rate_type=InterestRateTypeEnum.NMV,
        term_months=1, payment_modality=PaymentModalityEnum.FIXED_INSTALLMENT,
        status=LoanStatusEnum.CURRENT
    )
    
    # Due date is Jan 15th, 2024
    sched = AmortizationSchedule(
        id=uuid4(), loan_id=loan.id, installment_number=1, due_date=datetime.date(2024, 1, 15),
        principal_payment=Decimal('1000'), interest_payment=Decimal('20'),
        life_insurance=Decimal('0'), other_charges=Decimal('0'),
        total_installment_amount=Decimal('1020'), principal_balance=Decimal('1000'), is_paid=False
    )
    loan.amortization_schedule = [sched]
    
    return loan


@freeze_time("2024-01-10")
def test_arrears_before_due_date(mock_loan):
    """If today is before due_date, arrears should be 0."""
    today = datetime.date.today()
    days = StatementCalculator.calculate_days_in_arrears(mock_loan, today)
    assert days == 0


@freeze_time("2024-01-20")
def test_arrears_after_due_date(mock_loan):
    """If today is 5 days after Jan 15, arrears should be 5."""
    today = datetime.date.today()
    days = StatementCalculator.calculate_days_in_arrears(mock_loan, today)
    assert days == 5


@freeze_time("2024-01-16")
def test_default_interest_calculation(mock_loan):
    """Test 1 day in arrears with 30% EA Max Usury Rate."""
    days_arrears = 1
    usury_ea = Decimal('0.30')
    default_int = StatementCalculator.calculate_default_interest(mock_loan, days_arrears, usury_ea)
    
    # Overdue principal is 1000. 
    # Daily penalty rate from 30% EA should be > 0.
    # 1000 * daily_penalty * 1 day = approx 0.72 depending on math roundings.
    assert default_int > Decimal('0')
    assert default_int < Decimal('1.00')

@freeze_time("2024-01-31")
def test_accrued_interest_past_due(mock_loan):
    """If past due, accrued is the full installment interest."""
    today = datetime.date.today()
    accrued = StatementCalculator.calculate_accrued_interest_pending(mock_loan, today)
    # The installment is past due, so it generated the full 20.00 interest inside that period
    assert accrued == Decimal('20')
