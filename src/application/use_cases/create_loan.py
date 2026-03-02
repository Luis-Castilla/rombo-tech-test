from dataclasses import dataclass
from typing import Dict, Any
from decimal import Decimal
from datetime import date
from uuid import UUID
import logging

from src.domain.services.loan_simulator import LoanSimulator
from src.domain.services.accounting_factory import AccountingFactory
from src.domain.ports.output.usury_rate_service import IUsuryRateService
from src.domain.ports.output.unit_of_work import IUnitOfWork
from src.domain.entities.enums import InterestRateTypeEnum, PaymentModalityEnum
from src.domain.entities.loan import Loan

logger = logging.getLogger(__name__)

@dataclass
class CreateLoanRequestDTO:
    customer_id: str
    requested_amount: str
    interest_rate: str
    interest_rate_type: str
    term_months: int
    payment_modality: str

class CreateLoanUseCase:
    """
    Application use case for orchestrating the Loan Creation under an ACID transaction.
    """
    def __init__(self, uow: IUnitOfWork, usury_rate_service: IUsuryRateService):
        self.uow = uow
        self.usury_rate_service = usury_rate_service

    def execute(self, request_dto: CreateLoanRequestDTO) -> Dict[str, Any]:
        try:
            # 1. Input parsing to Domain Values
            customer_id = UUID(request_dto.customer_id)
            requested_amount = Decimal(request_dto.requested_amount)
            interest_rate = Decimal(request_dto.interest_rate)
            rate_type = InterestRateTypeEnum[request_dto.interest_rate_type]
            term_months = int(request_dto.term_months)
            payment_modality = PaymentModalityEnum[request_dto.payment_modality]
        except (ValueError, KeyError, TypeError) as e:
            raise ValueError(f"Invalid input data: {str(e)}")

        # 2. Start Unit of Work (Transactional Boundary BEGIN)
        with self.uow:
            # 3. Domain Check: Customer Eligibility
            customer = self.uow.customers.get_by_id(customer_id)
            if not customer:
                raise ValueError(f"Customer with ID {customer_id} not found.")

            has_arrears = self.uow.loans.has_active_loans_in_arrears(customer_id)
            
            if not customer.meets_eligibility_criteria(requested_amount, has_arrears):
                raise ValueError(
                    "Customer is not eligible for this loan. Check Credit Score (>600), "
                    "absence of arrears, and borrowing capacity."
                )

            # 4. Domain Check: Usury Rate Compliance
            if not self.usury_rate_service.is_rate_legal(interest_rate, rate_type):
                raise ValueError(f"The requested interest rate exceeds the legal Usury Limit.")

            # 5. Core Domain Logic: Create Loan Root Entity
            new_loan = Loan(
                customer_id=customer_id,
                requested_amount=requested_amount,
                approved_amount=requested_amount,
                interest_rate=interest_rate,
                interest_rate_type=rate_type,
                term_months=term_months,
                payment_modality=payment_modality
            )
            
            # 6. Core Domain Logic: Generate Amortization Schedule
            schedule_entities = LoanSimulator.generate_schedule(
                requested_amount=requested_amount,
                interest_rate=interest_rate,
                rate_type=rate_type,
                term_months=term_months,
                payment_modality=payment_modality,
                start_date=date.today()
            )
            
            # Link schedule to the newly generated Loan ID
            for installment in schedule_entities:
                installment.loan_id = new_loan.id
            new_loan.amortization_schedule = schedule_entities

            # 7. Core Domain Logic: Accounting Entry for Disbursement
            journal_entry = AccountingFactory.create_loan_disbursement_journal(
                loan_id=new_loan.id, 
                amount=requested_amount
            )

            # 8. Persist inside UoW
            self.uow.loans.save(new_loan)
            self.uow.accounting.save_journal_entry(journal_entry)
            
            # 9. Commit Transaction Block!
            self.uow.commit()

            logger.info(f"Loan {new_loan.id} successfully created and disbursed globally.")

            return {
                "loan_id": str(new_loan.id),
                "status": new_loan.status.value,
                "approved_amount": str(new_loan.approved_amount)
            }
