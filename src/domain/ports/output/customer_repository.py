from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from src.domain.entities.customer import Customer

class ICustomerRepository(ABC):
    @abstractmethod
    def get_by_id(self, customer_id: UUID) -> Optional[Customer]:
        pass
