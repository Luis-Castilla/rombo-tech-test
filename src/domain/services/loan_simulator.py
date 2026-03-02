from decimal import Decimal, ROUND_HALF_UP
from typing import List
from datetime import date
from dateutil.relativedelta import relativedelta
from src.domain.entities.loan import AmortizationSchedule
from src.domain.entities.enums import InterestRateTypeEnum, PaymentModalityEnum
from uuid import uuid4

class LoanSimulator:
    """
    Domain service for simulating loan amortization schedules.
    All calculations are done strictly with decimal.Decimal.
    """

    @staticmethod
    def _convert_to_monthly_rate(interest_rate: Decimal, rate_type: InterestRateTypeEnum) -> Decimal:
        """
        Converts the provided interest rate to a periodic monthly rate (i).
        NMV -> Nominal Mes Vencido (rate / 12)
        EAR -> Efectiva Anual ((1 + rate)^(1/12) - 1)
        """
        if rate_type == InterestRateTypeEnum.NMV:
            return (interest_rate / Decimal('12')).quantize(Decimal('1.000000'))
        elif rate_type == InterestRateTypeEnum.EAR:
            one_plus_ea = Decimal('1') + interest_rate
            exponent = Decimal('1') / Decimal('12')
            
            periodic_rate = (exponent * one_plus_ea.ln()).exp() - Decimal('1')
            
            return periodic_rate.quantize(Decimal('1.000000'))
        else:
            raise ValueError(f"Unsupported interest rate type: {rate_type}")

    @classmethod
    def generate_schedule(cls,
                          requested_amount: Decimal,
                          interest_rate: Decimal,
                          rate_type: InterestRateTypeEnum,
                          term_months: int,
                          payment_modality: PaymentModalityEnum,
                          start_date: date = None) -> List[AmortizationSchedule]:
        
        if requested_amount <= 0:
            raise ValueError("Requested amount must be greater than zero.")
        if term_months <= 0:
            raise ValueError("Term must be greater than zero.")
        if interest_rate < 0:
            raise ValueError("Interest rate cannot be negative.")

        start_date = start_date or date.today()
        monthly_rate = cls._convert_to_monthly_rate(interest_rate, rate_type)
        
        schedule = []
        principal_balance = requested_amount
        loan_id = uuid4() # Dummy UUID for simulation

        # If rate is 0, special case
        if monthly_rate == Decimal('0'):
            fixed_payment = (requested_amount / Decimal(term_months)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            for i in range(1, term_months + 1):
                due_date = start_date + relativedelta(months=i)
                principal_payment = fixed_payment if i < term_months else principal_balance
                principal_balance -= principal_payment
                
                installment = AmortizationSchedule(
                    loan_id=loan_id,
                    installment_number=i,
                    due_date=due_date,
                    principal_payment=principal_payment,
                    interest_payment=Decimal('0.00'),
                    life_insurance=Decimal('0.00'),
                    other_charges=Decimal('0.00'),
                    total_installment_amount=principal_payment,
                    principal_balance=max(Decimal('0.00'), principal_balance)
                )
                schedule.append(installment)
            return schedule

        if payment_modality == PaymentModalityEnum.FIXED_INSTALLMENT:
            one_plus_i_n = (Decimal('1') + monthly_rate) ** term_months
            numerator = requested_amount * monthly_rate * one_plus_i_n
            denominator = one_plus_i_n - Decimal('1')
            fixed_installment = (numerator / denominator).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            for i in range(1, term_months + 1):
                due_date = start_date + relativedelta(months=i)
                interest_payment = (principal_balance * monthly_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                
                if i == term_months:
                    principal_payment = principal_balance
                    total_installment = principal_payment + interest_payment
                else:
                    principal_payment = fixed_installment - interest_payment
                    total_installment = fixed_installment
                
                principal_balance -= principal_payment

                installment = AmortizationSchedule(
                    loan_id=loan_id,
                    installment_number=i,
                    due_date=due_date,
                    principal_payment=principal_payment,
                    interest_payment=interest_payment,
                    life_insurance=Decimal('0.00'),
                    other_charges=Decimal('0.00'),
                    total_installment_amount=total_installment,
                    principal_balance=max(Decimal('0.00'), principal_balance)
                )
                schedule.append(installment)

        elif payment_modality == PaymentModalityEnum.CONSTANT_PRINCIPAL:
            constant_principal = (requested_amount / Decimal(term_months)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            for i in range(1, term_months + 1):
                due_date = start_date + relativedelta(months=i)
                interest_payment = (principal_balance * monthly_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                
                if i == term_months:
                    principal_payment = principal_balance
                else:
                    principal_payment = constant_principal
                
                total_installment = principal_payment + interest_payment
                principal_balance -= principal_payment

                installment = AmortizationSchedule(
                    loan_id=loan_id,
                    installment_number=i,
                    due_date=due_date,
                    principal_payment=principal_payment,
                    interest_payment=interest_payment,
                    life_insurance=Decimal('0.00'),
                    other_charges=Decimal('0.00'),
                    total_installment_amount=total_installment,
                    principal_balance=max(Decimal('0.00'), principal_balance)
                )
                schedule.append(installment)
        else:
            raise ValueError(f"Unsupported payment modality: {payment_modality}")

        return schedule
