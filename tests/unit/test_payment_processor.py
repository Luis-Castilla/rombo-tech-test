from decimal import Decimal
import pytest
from uuid import uuid4
import datetime
from src.domain.entities.loan import Loan, AmortizationSchedule, LoanStatusEnum
from src.domain.entities.enums import InterestRateTypeEnum, PaymentModalityEnum
from src.domain.services.payment_processor import PaymentProcessor, LoanAlreadyPaidError

def test_exact_payment_cascade():
    loan = Loan(
        id=uuid4(), customer_id=uuid4(), requested_amount=Decimal('1000'), 
        interest_rate=Decimal('0.02'), interest_rate_type=InterestRateTypeEnum.NMV,
        term_months=1, payment_modality=PaymentModalityEnum.FIXED_INSTALLMENT,
        status=LoanStatusEnum.CURRENT
    )
    
    # 1 Amortization schedule exactly 100
    sched = AmortizationSchedule(
        id=uuid4(), loan_id=loan.id, installment_number=1, due_date=datetime.date.today(),
        principal_payment=Decimal('50'), interest_payment=Decimal('30'),
        life_insurance=Decimal('10'), other_charges=Decimal('10'),
        total_installment_amount=Decimal('100'), principal_balance=Decimal('50'), is_paid=False
    )
    loan.amortization_schedule = [sched]
    
    unallocated, allocs = PaymentProcessor.process(loan, Decimal('100'))
    
    assert unallocated == Decimal('0')
    assert len(allocs) == 1
    assert allocs[0].legal_fees_amount == Decimal('10')
    assert allocs[0].insurance_amount == Decimal('10')
    assert allocs[0].ordinary_interest_amount == Decimal('30')
    assert allocs[0].principal_amount == Decimal('50')
    
    assert sched.is_paid is True
    assert sched.principal_balance == Decimal('0')
    assert loan.status == LoanStatusEnum.PAID


def test_partial_payment_exhausts_priority():
    loan = Loan(
        id=uuid4(), customer_id=uuid4(), requested_amount=Decimal('1000'), 
        interest_rate=Decimal('0.02'), interest_rate_type=InterestRateTypeEnum.NMV,
        term_months=1, payment_modality=PaymentModalityEnum.FIXED_INSTALLMENT,
        status=LoanStatusEnum.CURRENT
    )
    
    # Only paying 35 out of 100
    sched = AmortizationSchedule(
        id=uuid4(), loan_id=loan.id, installment_number=1, due_date=datetime.date.today(),
        principal_payment=Decimal('50'), interest_payment=Decimal('30'),
        life_insurance=Decimal('10'), other_charges=Decimal('10'),
        total_installment_amount=Decimal('100'), principal_balance=Decimal('50'), is_paid=False
    )
    loan.amortization_schedule = [sched]
    
    unallocated, allocs = PaymentProcessor.process(loan, Decimal('35'))
    
    assert unallocated == Decimal('0')
    
    # 10 to legal, 10 to insurance, 15 to interest, 0 to principal
    assert allocs[0].legal_fees_amount == Decimal('10')
    assert allocs[0].insurance_amount == Decimal('10')
    assert allocs[0].ordinary_interest_amount == Decimal('15')
    assert allocs[0].principal_amount == Decimal('0')
    
    assert sched.is_paid is False
    assert sched.other_charges == Decimal('0') # covered
    assert sched.life_insurance == Decimal('0') # covered
    assert sched.interest_payment == Decimal('15') # 30 - 15
    assert sched.principal_payment == Decimal('50') # untouched
