from abc import ABC, abstractmethod
from decimal import Decimal
from src.domain.entities.enums import InterestRateTypeEnum

class IUsuryRateService(ABC):
    """
    Port (Interface) for fetching or checking the mandated usury rate by the government.
    """
    
    @abstractmethod
    def is_rate_legal(self, requested_rate: Decimal, rate_type: InterestRateTypeEnum) -> bool:
        """
        Validates if the provided rate is compliant with the Max Usury policy.
        """
        pass
