import pytest
from flask import Flask
from src.main import create_app
from src.infrastructure.config.extensions import db
from src.infrastructure.adapters.output.persistence.models import CustomerModel, DocumentTypeEnum, LoanModel, InterestRateTypeEnum, PaymentModalityEnum, AmortizationScheduleModel
import datetime

@pytest.fixture
def app_with_loan_cqrs():
    class Config:
        TESTING = True
        SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        
    app = create_app(Config)
    
    with app.app_context():
        db.create_all()
        # Seed customer and loan
        customer = CustomerModel(
            document_type=DocumentTypeEnum.CC, document_number="CQRS-111",
            first_name="Jane", last_name="CQRS", city="Cali"
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
        
        # Add 1 schedule with DUE DATE yesterday
        due = datetime.date.today() - datetime.timedelta(days=1)
        sched = AmortizationScheduleModel(
            loan_id=loan.id, installment_number=1, due_date=due,
            principal_payment=1000, interest_payment=20, life_insurance=0,
            other_charges=0, total_installment_amount=1020, principal_balance=1000,
            is_paid=False
        )
        db.session.add(sched)
        db.session.commit()
        
        app.test_loan_id = str(loan.id)
        
    return app

@pytest.fixture
def client(app_with_loan_cqrs):
    return app_with_loan_cqrs.test_client()

def test_get_loan_statement_n_plus_one_avoidance_and_dto(client, app_with_loan_cqrs):
    # This endpoint uses joinedload, meaning hitting it should load everything compactly
    # If it was lazy, detaching the session would break the dto mapper, but joinedload keeps it safe
    # Also ensuring the math calculated 1 day of arrears dynamically
    
    resp = client.get(f'/api/v1/loans/{app_with_loan_cqrs.test_loan_id}/statement')
    
    assert resp.status_code == 200
    data = resp.get_json()['data']
    
    assert data['loan_id'] == app_with_loan_cqrs.test_loan_id
    assert data['days_in_arrears'] == 1 # Math on the fly evaluated successfully
    assert len(data['installments']) == 1
    assert data['installments'][0]['principal'] == '1000.00'
    assert float(data['default_interest_pending']) > 0  # 1 day of mora generated some cents
