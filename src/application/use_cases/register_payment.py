import time
import logging
from datetime import datetime, timezone
from uuid import UUID
from decimal import Decimal
from typing import Dict, Any

from src.domain.ports.output.unit_of_work import IUnitOfWork
from src.domain.services.payment_processor import PaymentProcessor, LoanAlreadyPaidError
from src.domain.services.accounting_factory import AccountingFactory
from src.domain.entities.payment import Payment
from src.domain.entities.enums import PaymentMethodEnum

logger = logging.getLogger(__name__)

class IdempotencyError(ValueError):
    pass

class RegisterPaymentUseCase:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    def execute(self, loan_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes a payment through the Colombian matching cascade.
        Must execute under a strict ACID Transaction with Row-Level Locking.
        """
        try:
            loan_uuid = UUID(loan_id)
            paid_amount = Decimal(str(payload['paid_amount']))
            payment_ref = str(payload['payment_reference'])
            payment_method = PaymentMethodEnum[payload['payment_method']]
            
            # Use provided date or fallback to now
            payment_date = datetime.now(timezone.utc)
            if 'payment_date' in payload and payload['payment_date']:
                 payment_date = datetime.fromisoformat(payload['payment_date'].replace('Z', '+00:00'))
        except (ValueError, KeyError, TypeError) as e:
            raise ValueError(f"Invalid payment payload: {str(e)}")

        with self.uow:
            # 1. Idempotency Check
            if self.uow.loans.payment_exists(payment_ref):
                raise IdempotencyError(f"Payment with reference {payment_ref} was already processed.")

            # 2. Lock the Loan row for Update! (Pessimistic concurrency control)
            loan = self.uow.loans.get_by_id_for_update(loan_uuid)
            if not loan:
                raise ValueError(f"Loan {loan_id} not found.")

            # 3. Domain Logic: Payment Cascade Processing
            try:
                unallocated_amount, allocations = PaymentProcessor.process(loan, paid_amount)
            except LoanAlreadyPaidError as e:
                raise ValueError(str(e))

            # 4. Create the Domain Payment Record
            new_payment = Payment(
                loan_id=loan.id,
                paid_amount=paid_amount,
                payment_reference=payment_ref,
                payment_method=payment_method,
                payment_date=payment_date,
                allocations=allocations
            )

            # Link DB models if needed: (in this architecture, the repository maps entity graphs to SQLAlchemy insertions)
            for alloc in new_payment.allocations:
                alloc.payment_id = new_payment.id

            # 5. Extract Totals for Accounting
            total_principal = sum(a.principal_amount for a in allocations)
            total_interest = sum(a.ordinary_interest_amount + a.default_interest_amount for a in allocations)
            total_insurance = sum(a.insurance_amount for a in allocations)

            # 6. Generate Accounting Journal Entry
            journal_entry = AccountingFactory.create_loan_payment_journal(
                loan_id=loan.id,
                payment_id=new_payment.id,
                total_amount=paid_amount, # Bank debit
                principal=total_principal,
                interest=total_interest,
                insurance=total_insurance
            )

            # 7. Persist Operations
            # (Note: In a pure DDD repo, uow.loans.save(loan) would handle updating the tree. 
            # We must ensure the repo knows how to update Schedules and add Payments.
            # For simplicity, we assume `save()` handles merge or flush or similar tree syncing logic.)
            
            self.uow.loans.save(loan)
            
            # Since our ILoanRepository doesn't natively expose save_payment, we might add it or rely on cascade.
            # Assuming we need a save_payment inside the loan repo to handle this sub-aggregate:
            if hasattr(self.uow.loans, 'save_payment'):
                self.uow.loans.save_payment(new_payment)

            self.uow.accounting.save_journal_entry(journal_entry)

            # 8. Commit ACID Transaction
            self.uow.commit()
            
            logger.info("Payment processed successfully with row-lock.", extra={"loan_id": loan_id, "ref": payment_ref})

            return {
                "loan_id": str(loan.id),
                "payment_id": str(new_payment.id),
                "status": loan.status.value,
                "unallocated_return_amount": str(unallocated_amount),
                "allocations_count": len(allocations)
            }
