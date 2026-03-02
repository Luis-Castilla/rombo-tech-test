from decimal import Decimal
from datetime import date
from src.domain.entities.loan import Loan, AmortizationSchedule

DAYS_IN_COMMERCIAL_MONTH = 30

class StatementCalculator:
    """
    Domain service for performing dynamic 'on-the-fly' calculations for the Loan Statement.
    """
    
    @staticmethod
    def calculate_days_in_arrears(loan: Loan, current_date: date) -> int:
        """
        Calculates the maximum days in arrears by looking at the oldest unpaid installment.
        """
        if loan.status.name == 'PAID':
            return 0
            
        unpaid = [s for s in loan.amortization_schedule if not s.is_paid]
        if not unpaid:
            return 0
            
        oldest_due = min(s.due_date for s in unpaid)
        delta = (current_date - oldest_due).days
        return max(0, delta)

    @staticmethod
    def calculate_accrued_interest_pending(loan: Loan, current_date: date) -> Decimal:
        """
        Calculates the proportion of ordinary interest generated from the last unpaid installment 
        date up to today. Simplified: daily rate * days elapsed * principal balance.
        """
        if loan.status.name == 'PAID':
            return Decimal('0')
            
        unpaid = sorted([s for s in loan.amortization_schedule if not s.is_paid], key=lambda x: x.installment_number)
        if not unpaid:
            return Decimal('0')
            
        current_installment = unpaid[0]
        
        # If today is before or equal to due date, calculate partial accrual
        # Assuming previous due date was 30 days before this one (simplified uniformly)
        # Note: In a real system, last_payment_date or previous installment due_date is used.
        import datetime
        previous_date = current_installment.due_date - datetime.timedelta(days=DAYS_IN_COMMERCIAL_MONTH)
        
        if current_date <= previous_date:
            return Decimal('0')
            
        days_elapsed = (current_date - previous_date).days
        
        # if in arrears, it accrued the whole installment interest already
        if days_elapsed >= DAYS_IN_COMMERCIAL_MONTH:
            return current_installment.interest_payment
            
        # Partial accrual (daily proportion)
        daily_interest = current_installment.interest_payment / Decimal(str(DAYS_IN_COMMERCIAL_MONTH))
        accrued = (daily_interest * Decimal(str(days_elapsed))).quantize(Decimal('0.01'))
        
        return min(accrued, current_installment.interest_payment)
        
    @staticmethod
    def calculate_default_interest(loan: Loan, days_in_arrears: int, usury_rate_ea: Decimal) -> Decimal:
        """
        Calculates default penalty interest (Mora) applying the max usury rate over the overdue principal.
        """
        if days_in_arrears <= 0 or loan.status.name == 'PAID':
            return Decimal('0')
            
        unpaid = [s for s in loan.amortization_schedule if not s.is_paid and s.due_date < date.today()]
        if not unpaid:
            return Decimal('0')
            
        # Arrears apply usually on the over-due principal installment amount
        overdue_principal = sum(s.principal_payment for s in unpaid)
        
        # Daily penalty rate based on EA Usury -> Nominal -> Daily
        # (1 + EA)^(1/365) - 1
        base = Decimal('1') + usury_rate_ea
        exponent = Decimal('1') / Decimal('365')
        daily_penalty_rate = (exponent * base.ln()).exp() - Decimal('1')
        
        default_interest = (overdue_principal * daily_penalty_rate * Decimal(str(days_in_arrears))).quantize(Decimal('0.01'))
        return default_interest
