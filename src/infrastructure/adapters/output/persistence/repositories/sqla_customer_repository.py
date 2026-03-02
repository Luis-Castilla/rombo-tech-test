from typing import Optional
from uuid import UUID
from src.domain.ports.output.customer_repository import ICustomerRepository
from src.domain.entities.customer import Customer
from src.infrastructure.adapters.output.persistence.models import CustomerModel

class SqlAlchemyCustomerRepository(ICustomerRepository):
    def __init__(self, session):
        self.session = session

    def get_by_id(self, customer_id: UUID) -> Optional[Customer]:
        model = self.session.query(CustomerModel).filter_by(id=customer_id).first()
        if not model:
            return None
            
        return Customer(
            id=model.id,
            document_type=model.document_type,
            document_number=model.document_number,
            first_name=model.first_name,
            last_name=model.last_name,
            city=model.city,
            email=model.email,
            phone_number=model.phone_number,
            credit_score=model.credit_score,
            borrowing_capacity=model.borrowing_capacity if hasattr(model, 'borrowing_capacity') else 0, # Assuming capacity comes from model or elsewhere
            risk_classification=model.risk_classification,
            created_at=model.created_at
        )
