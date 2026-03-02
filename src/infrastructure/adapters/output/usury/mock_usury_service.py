from decimal import Decimal
from src.domain.entities.enums import InterestRateTypeEnum
from src.domain.ports.output.usury_rate_service import IUsuryRateService

class MockUsuryRateService(IUsuryRateService):
    """
    Mock adapter representing a call to the Superfinanciera for the EA usury limit.
    """
    def __init__(self, current_ea_limit: Decimal = Decimal('0.3150')):
        self.current_ea_limit = current_ea_limit

    def is_rate_legal(self, requested_rate: Decimal, rate_type: InterestRateTypeEnum) -> bool:
        # Convert NMV to EA to compare apples to apples
        if rate_type == InterestRateTypeEnum.NMV:
            # Formula: EA = (1 + NMV)^12 - 1
            # Using continuous limits via Decimal math.
            base = Decimal('1') + requested_rate
            exponent = Decimal('12')
            
            # Since exponent is integer, we can actually use ** in python Decimal for this!
            equivalent_ea = (base ** exponent) - Decimal('1')
        else:
            equivalent_ea = requested_rate
            
        return equivalent_ea <= self.current_ea_limit
