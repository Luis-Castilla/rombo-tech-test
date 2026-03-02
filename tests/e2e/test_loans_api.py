import pytest
from src.main import create_app

@pytest.fixture
def client():
    # Minimal configuration config without real DB dependency
    class Config:
        TESTING = True
        SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        
    app = create_app(Config)
    with app.test_client() as client:
        yield client

def test_simulate_loan_success(client):
    payload = {
        "requested_amount": "5000000",
        "interest_rate": "0.15",
        "interest_rate_type": "EAR",
        "term_months": 24,
        "payment_modality": "FIXED_INSTALLMENT",
        "start_date": "2024-01-01"
    }

    response = client.post('/api/v1/loans/simulate', json=payload)
    assert response.status_code == 200
    
    data = response.get_json()
    assert "summary" in data
    assert "amortization_schedule" in data
    assert len(data["amortization_schedule"]) == 24
    assert data["summary"]["requested_amount"] == "5000000"

def test_simulate_loan_invalid_payload_triggers_400(client):
    payload = {
        "requested_amount": "-5000",  # Negative amount should be caught by domain math validation
        "interest_rate": "0.15",
        "interest_rate_type": "EAR",
        "term_months": 24,
        "payment_modality": "FIXED_INSTALLMENT"
    }

    response = client.post('/api/v1/loans/simulate', json=payload)
    assert response.status_code == 400
    
    data = response.get_json()
    assert data["error"] == "Bad Request"
    assert "Requested amount must be greater than zero" in data["message"]

def test_simulate_loan_missing_field_triggers_400(client):
    payload = {
        "requested_amount": "5000000",
        # intentionally missing 'interest_rate' to trigger KeyError inside Use Case -> ValueError map
        "interest_rate_type": "EAR",
        "term_months": 24,
        "payment_modality": "FIXED_INSTALLMENT"
    }

    response = client.post('/api/v1/loans/simulate', json=payload)
    assert response.status_code == 400
    
    data = response.get_json()
    assert data["error"] == "Bad Request"
    assert "Missing required field" in data["message"]
