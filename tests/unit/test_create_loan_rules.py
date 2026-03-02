import pytest
from decimal import Decimal
from src.domain.entities.customer import Customer
from src.domain.entities.enums import DocumentTypeEnum, InterestRateTypeEnum
from src.infrastructure.adapters.output.usury.mock_usury_service import MockUsuryRateService

def test_customer_eligibility_score_too_low():
    customer = Customer(
        document_type=DocumentTypeEnum.CC,
        document_number="123",
        first_name="Test",
        last_name="Score",
        city="Bogota",
        credit_score=599, # Fails check
        borrowing_capacity=Decimal('10000000')
    )
    assert not customer.meets_eligibility_criteria(Decimal('1000000'), has_arrears=False)

def test_customer_eligibility_has_arrears():
    customer = Customer(
        document_type=DocumentTypeEnum.CC,
        document_number="123",
        first_name="Test",
        last_name="Mora",
        city="Bogota",
        credit_score=800,
        borrowing_capacity=Decimal('10000000')
    )
    assert not customer.meets_eligibility_criteria(Decimal('1000000'), has_arrears=True)

def test_customer_eligibility_insufficient_capacity():
    customer = Customer(
        document_type=DocumentTypeEnum.CC,
        document_number="123",
        first_name="Test",
        last_name="Money",
        city="Bogota",
        credit_score=800,
        borrowing_capacity=Decimal('5000000') # Lower than requested!
    )
    assert not customer.meets_eligibility_criteria(Decimal('8000000'), has_arrears=False)

def test_usury_rate_mock_service():
    service = MockUsuryRateService(current_ea_limit=Decimal('0.3150')) # 31.5% EA Limit
    
    # 2% NMV -> equivalent EA is roughly ~26.8% EA -> Legal
    assert service.is_rate_legal(Decimal('0.02'), InterestRateTypeEnum.NMV) is True
    
    # 3% NMV -> equivalent EA is roughly ~42.5% EA -> Illegal!
    assert service.is_rate_legal(Decimal('0.03'), InterestRateTypeEnum.NMV) is False
    
    # 30% EAR directly -> Legal
    assert service.is_rate_legal(Decimal('0.30'), InterestRateTypeEnum.EAR) is True
    
    # 35% EAR directly -> Illegal!
    assert service.is_rate_legal(Decimal('0.35'), InterestRateTypeEnum.EAR) is False
