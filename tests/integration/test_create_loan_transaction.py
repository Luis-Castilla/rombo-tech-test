import pytest
from flask import Flask
from src.main import create_app
from src.infrastructure.config.extensions import db
from src.infrastructure.adapters.output.persistence.models import CustomerModel, DocumentTypeEnum, LoanModel, JournalEntryModel

@pytest.fixture
def app():
    class Config:
        TESTING = True
        SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        
    app = create_app(Config)
    
    with app.app_context():
        db.create_all()
        # Seed a valid customer for testing
        test_customer = CustomerModel(
            document_type=DocumentTypeEnum.CC,
            document_number="999888777",
            first_name="John",
            last_name="Doe",
            city="Bogota",
            credit_score=850,
            borrowing_capacity=50000000
        )
        db.session.add(test_customer)
        db.session.commit()
        # Attach customer_id to app for tests to use
        app.test_customer_id = str(test_customer.id)
        
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_db_rollback_on_accounting_failure(client, app, monkeypatch):
    """
    Critical Integration Test: We monkeypatch the Database Session.commit 
    to force an Exception ONLY during the final transaction commit phase.
    We must ensure no Loan, Amortization, or JournalEntry is left in the DB.
    """
    # 1. Start with exactly 0 loans and 0 journal entries
    with app.app_context():
        assert LoanModel.query.count() == 0
        assert JournalEntryModel.query.count() == 0

    # 2. Mock 'commit' to suddenly fail
    def mock_failing_commit(*args, **kwargs):
        raise Exception("MOCKED DATABASE CRASH DURING COMMIT")
        
    monkeypatch.setattr("sqlalchemy.orm.Session.commit", mock_failing_commit)

    # 3. Payload that would otherwise be perfectly valid
    payload = {
        "customer_id": app.test_customer_id,
        "requested_amount": "1000000",
        "interest_rate": "0.15",
        "interest_rate_type": "EAR",
        "term_months": 12,
        "payment_modality": "FIXED_INSTALLMENT"
    }

    # 4. Fire the POST request
    response = client.post('/api/v1/loans', json=payload)
    
    # HTTP 500 expected because our unhandled MOCKED Exception reaches the global error handler
    assert response.status_code == 500 

    # 5. Verify Rollback! The DB should STILL have exactly 0 loans and 0 journals
    with app.app_context():
        # The rollback is triggered automatically by SQLAlchemy when an Exception goes up 
        # out of the request context, ensuring ACID compliance.
        assert LoanModel.query.count() == 0
        assert JournalEntryModel.query.count() == 0
