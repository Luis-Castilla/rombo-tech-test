from dataclasses import dataclass
from typing import List, Dict, Any
from decimal import Decimal
from datetime import date
from src.domain.services.loan_simulator import LoanSimulator
from src.domain.entities.enums import InterestRateTypeEnum, PaymentModalityEnum

@dataclass
class SimulateLoanRequestDTO:
    requested_amount: str
    interest_rate: str
    interest_rate_type: str
    term_months: int
    payment_modality: str
    start_date: str = None  # YYYY-MM-DD

class SimulateLoanUseCase:
    """
    Application use case to orchestrate the simulation of a loan.
    It takes DTO request, maps to domain enums/Decimals, generates the schedule,
    and formats the output to dictionaries.
    """
    
    def execute(self, request_dto: SimulateLoanRequestDTO) -> Dict[str, Any]:
        try:
            # Domain mapping
            requested_amount = Decimal(request_dto.requested_amount)
            interest_rate = Decimal(request_dto.interest_rate)
            rate_type = InterestRateTypeEnum[request_dto.interest_rate_type]
            payment_modality = PaymentModalityEnum[request_dto.payment_modality]
            
            start_date = None
            if request_dto.start_date:
                start_date = date.fromisoformat(request_dto.start_date)

        except (ValueError, KeyError, TypeError) as e:
            raise ValueError(f"Invalid input data: {str(e)}")

        # Domain Logic Execution
        schedule_entities = LoanSimulator.generate_schedule(
            requested_amount=requested_amount,
            interest_rate=interest_rate,
            rate_type=rate_type,
            term_months=request_dto.term_months,
            payment_modality=payment_modality,
            start_date=start_date
        )

        # Presentation Mapping (Formatting for JSON output)
        total_principal = Decimal('0')
        total_interest = Decimal('0')
        installments = []

        for installment in schedule_entities:
            total_principal += installment.principal_payment
            total_interest += installment.interest_payment
            
            installments.append({
                "installment_number": installment.installment_number,
                "due_date": installment.due_date.isoformat(),
                "principal_payment": str(installment.principal_payment),
                "interest_payment": str(installment.interest_payment),
                "life_insurance": str(installment.life_insurance),
                "other_charges": str(installment.other_charges),
                "total_installment_amount": str(installment.total_installment_amount),
                "principal_balance": str(installment.principal_balance)
            })

        return {
            "summary": {
                "requested_amount": str(requested_amount),
                "total_paid_principal": str(total_principal),
                "total_paid_interest": str(total_interest),
                "total_paid": str(total_principal + total_interest)
            },
            "amortization_schedule": installments
        }
