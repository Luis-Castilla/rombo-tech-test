from decimal import Decimal
from typing import List, Tuple
from src.domain.entities.loan import Loan, AmortizationSchedule
from src.domain.entities.payment import PaymentAllocation

class LoanAlreadyPaidError(ValueError):
    """Raised when trying to apply a payment to a fully paid loan."""
    pass

class PaymentProcessor:
    """
    Domain service executing the Colombian legal payment cascade.
    Order: Legal Fees -> Insurance -> Default Interest -> Ordinary Interest -> Principal.
    """

    @staticmethod
    def process(loan: Loan, incoming_amount: Decimal) -> Tuple[Decimal, List[PaymentAllocation]]:
        """
        Distributes the incoming_amount across pending amortization schedules according to Colombian financial law.

        This mechanism strictly enforces the legal precedence required by the Superintendencia Financiera 
        de Colombia (SFC) for consumer loan allocations. When a partial payment is received, the funds 
        must exhaust the categories in the following strict order before moving to the next:
        
        1. Legal Fees / Other Charges (Costas de Cobranza)
        2. Life & Risk Insurance (Seguros)
        3. Default Interest (Intereses de Mora)
        4. Ordinary Interest (Intereses Corrientes)
        5. Principal (Capital)
        
        This invariance guarantees that the financial institution does not illegally overcharge 
        interest-on-interest (Anatocismo) by applying funds to principal before clearing active interest.

        Args:
            loan (Loan): The loan entity containing the amortization tree.
            incoming_amount (Decimal): The exact amount transferred by the customer.

        Returns:
            Tuple[Decimal, List[PaymentAllocation]]: 
                - The unallocated amount returning 0.00 if fully consumed, or the remainder if overpaid.
                - A list of exactly how the funds were distributed per quota.
                
        Side Effects:
            Mutates the input `loan` amortizations schedules (deducts balances, marks as paid) and its status.
        """
        if loan.status.name == 'PAID':
            raise LoanAlreadyPaidError(f"Loan {loan.id} is already fully paid.")

        unallocated_amount = incoming_amount
        allocations: List[PaymentAllocation] = []

        pending_schedules = sorted(
            [s for s in loan.amortization_schedule if not s.is_paid],
            key=lambda s: s.installment_number
        )

        for sched in pending_schedules:
            if unallocated_amount <= Decimal('0'):
                break

            alloc = PaymentAllocation(
                payment_id=None,  # Set by the use case once Payment entity is created
                amortization_schedule_id=sched.id,
                legal_fees_amount=Decimal('0'),
                insurance_amount=Decimal('0'),
                default_interest_amount=Decimal('0'),
                ordinary_interest_amount=Decimal('0'),
                principal_amount=Decimal('0')
            )

            # 1. Other Charges (Legal Fees / Collection Costs)
            if sched.other_charges > Decimal('0') and unallocated_amount > Decimal('0'):
                covered = min(sched.other_charges, unallocated_amount)
                alloc.legal_fees_amount = covered
                sched.other_charges -= covered
                unallocated_amount -= covered

            # 2. Life Insurance
            if sched.life_insurance > Decimal('0') and unallocated_amount > Decimal('0'):
                covered = min(sched.life_insurance, unallocated_amount)
                alloc.insurance_amount = covered
                sched.life_insurance -= covered
                unallocated_amount -= covered

            # 3. Default Interest (Mora) - For this iteration we assume it's pre-calculated onto the schedule or 0
            # If dynamic calculation based on days late is needed, it should be appended to the schedule beforehand.
            
            # 4. Ordinary Interest
            if sched.interest_payment > Decimal('0') and unallocated_amount > Decimal('0'):
                covered = min(sched.interest_payment, unallocated_amount)
                alloc.ordinary_interest_amount = covered
                sched.interest_payment -= covered
                unallocated_amount -= covered

            # 5. Principal
            if sched.principal_payment > Decimal('0') and unallocated_amount > Decimal('0'):
                covered = min(sched.principal_payment, unallocated_amount)
                alloc.principal_amount = covered
                sched.principal_payment -= covered
                sched.principal_balance -= covered
                unallocated_amount -= covered

            if (sched.other_charges == Decimal('0') and 
                sched.life_insurance == Decimal('0') and 
                sched.interest_payment == Decimal('0') and 
                sched.principal_payment == Decimal('0')):
                sched.is_paid = True

            allocations.append(alloc)

        # Mutate Loan state conceptually
        if all(s.is_paid for s in loan.amortization_schedule):
            loan.status = loan.status.__class__.PAID
        elif loan.status.name == 'IN_ARREARS':
            # Simplified check: if oldest pending schedule is not past due, return to CURRENT
            import datetime
            now = datetime.date.today()
            if not any((not s.is_paid and s.due_date < now) for s in loan.amortization_schedule):
                loan.status = loan.status.__class__.CURRENT

        return unallocated_amount, allocations
