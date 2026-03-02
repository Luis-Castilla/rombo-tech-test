import pytest
from flask import Flask
from src.main import create_app
from src.infrastructure.config.extensions import db
from src.infrastructure.adapters.output.persistence.models import CustomerModel, DocumentTypeEnum, LoanModel, JournalEntryModel, InterestRateTypeEnum, PaymentModalityEnum, AmortizationScheduleModel
import uuid

@pytest.fixture
def app_with_loan():
    class Config:
        TESTING = True
        SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        
    app = create_app(Config)
    
    with app.app_context():
        db.create_all()
        # Seed customer and loan
        customer = CustomerModel(
            document_type=DocumentTypeEnum.CC, document_number="111",
            first_name="Jane", last_name="Doe", city="Cali"
        )
        db.session.add(customer)
        db.session.commit()
        
        loan = LoanModel(
            customer_id=customer.id, requested_amount=1000, approved_amount=1000,
            interest_rate=0.02, interest_rate_type=InterestRateTypeEnum.NMV,
            term_months=1, payment_modality=PaymentModalityEnum.FIXED_INSTALLMENT
        )
        db.session.add(loan)
        db.session.commit()
        
        # Add 1 schedule
        import datetime
        sched = AmortizationScheduleModel(
            loan_id=loan.id, installment_number=1, due_date=datetime.date(2024, 1, 1),
            principal_payment=1000, interest_payment=20, life_insurance=0,
            other_charges=0, total_installment_amount=1020, principal_balance=1000,
            is_paid=False
        )
        db.session.add(sched)
        db.session.commit()
        
        app.test_loan_id = str(loan.id)
        
    return app

@pytest.fixture
def client(app_with_loan):
    return app_with_loan.test_client()

def test_idempotency_duplicate_payment(client, app_with_loan):
    payload = {
        "paid_amount": "1020",
        "payment_method": "PSE",
        "payment_reference": "TX-999-UNIQUE"
    }

    # First request: should succeed 201
    resp1 = client.post(f'/api/v1/loans/{app_with_loan.test_loan_id}/payments', json=payload)
    assert resp1.status_code == 201
    
    # Second request exactly identical reference: should return 409 Conflict
    resp2 = client.post(f'/api/v1/loans/{app_with_loan.test_loan_id}/payments', json=payload)
    assert resp2.status_code == 409
    assert "Conflict" in resp2.get_json()['error']
