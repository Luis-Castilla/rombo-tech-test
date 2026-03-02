import pytest
from decimal import Decimal
from src.domain.services.loan_simulator import LoanSimulator
from src.domain.entities.enums import InterestRateTypeEnum, PaymentModalityEnum

def test_simulator_fixed_installment():
    # Simulate $1,000,000 at 18% NMV for 12 months using purely financial math inside the domain!
    schedule = LoanSimulator.generate_schedule(
        requested_amount=Decimal('1000000'),
        interest_rate=Decimal('0.18'), 
        rate_type=InterestRateTypeEnum.NMV,
        term_months=12,
        payment_modality=PaymentModalityEnum.FIXED_INSTALLMENT
    )
    
    assert len(schedule) == 12
    assert schedule[-1].principal_balance == Decimal('0.00')
    
    total_principal_paid = sum(s.principal_payment for s in schedule)
    assert total_principal_paid == Decimal('1000000.00')

def test_simulator_constant_principal():
    # Simulate $1,200,000 at 12% NMV for 12 months -> abono a capital is 100,000 per month
    schedule = LoanSimulator.generate_schedule(
        requested_amount=Decimal('1200000'),
        interest_rate=Decimal('0.12'),
        rate_type=InterestRateTypeEnum.NMV,
        term_months=12,
        payment_modality=PaymentModalityEnum.CONSTANT_PRINCIPAL
    )
    
    assert len(schedule) == 12
    assert schedule[0].principal_payment == Decimal('100000.00')
    assert schedule[-1].principal_balance == Decimal('0.00')
    
    # 1.2M * (0.12/12) = 1.2M * 0.01 = 12,000
    assert schedule[0].interest_payment == Decimal('12000.00')
    
def test_value_errors_on_negative_or_zero_values():
    with pytest.raises(ValueError):
        LoanSimulator.generate_schedule(
            requested_amount=Decimal('-1000'), # Invalid amount!
            interest_rate=Decimal('0.1'),
            rate_type=InterestRateTypeEnum.EAR,
            term_months=12,
            payment_modality=PaymentModalityEnum.FIXED_INSTALLMENT
        )
