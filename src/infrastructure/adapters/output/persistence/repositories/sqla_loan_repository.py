from uuid import UUID
from src.domain.ports.output.loan_repository import ILoanRepository
from src.domain.entities.loan import Loan
from src.infrastructure.adapters.output.persistence.models import LoanModel, AmortizationScheduleModel, LoanStatusEnum

class SqlAlchemyLoanRepository(ILoanRepository):
    def __init__(self, session):
        self.session = session

    def has_active_loans_in_arrears(self, customer_id: UUID) -> bool:
        count = self.session.query(LoanModel).filter_by(
            customer_id=customer_id, 
            status=LoanStatusEnum.IN_ARREARS
        ).count()
        return count > 0

    def save(self, loan: Loan) -> None:
        loan_model = self.session.query(LoanModel).filter_by(id=loan.id).first()
        is_new = False
        if not loan_model:
            loan_model = LoanModel(id=loan.id)
            is_new = True
            
        loan_model.customer_id = loan.customer_id
        loan_model.requested_amount = loan.requested_amount
        loan_model.approved_amount = loan.approved_amount
        loan_model.interest_rate = loan.interest_rate
        loan_model.interest_rate_type = loan.interest_rate_type
        loan_model.term_months = loan.term_months
        loan_model.payment_modality = loan.payment_modality
        loan_model.status = loan.status
        loan_model.application_date = loan.application_date
        loan_model.disbursement_date = loan.disbursement_date

        if is_new:
            self.session.add(loan_model)

        # Upsert schedules
        from src.infrastructure.adapters.output.persistence.models import AmortizationScheduleModel
        for sched in loan.amortization_schedule:
            sched_model = self.session.query(AmortizationScheduleModel).filter_by(id=sched.id).first()
            is_new_sched = False
            if not sched_model:
                sched_model = AmortizationScheduleModel(id=sched.id)
                is_new_sched = True
                
            sched_model.loan_id = sched.loan_id
            sched_model.installment_number = sched.installment_number
            sched_model.due_date = sched.due_date
            sched_model.principal_payment = sched.principal_payment
            sched_model.interest_payment = sched.interest_payment
            sched_model.life_insurance = sched.life_insurance
            sched_model.other_charges = sched.other_charges
            sched_model.total_installment_amount = sched.total_installment_amount
            sched_model.principal_balance = sched.principal_balance
            sched_model.is_paid = sched.is_paid
            
            if is_new_sched:
                self.session.add(sched_model)

    def get_by_id_for_update(self, loan_id: UUID) -> Optional[Loan]:
        model = self.session.query(LoanModel).with_for_update().filter_by(id=loan_id).first()
        if not model:
            return None
            
        loan = Loan(
            id=model.id,
            customer_id=model.customer_id,
            requested_amount=model.requested_amount,
            approved_amount=model.approved_amount,
            interest_rate=model.interest_rate,
            interest_rate_type=model.interest_rate_type,
            term_months=model.term_months,
            payment_modality=model.payment_modality,
            status=model.status,
            application_date=model.application_date,
            disbursement_date=model.disbursement_date
        )
        
        # Load schedules
        from src.domain.entities.loan import AmortizationSchedule
        schedule_entities = []
        for sched_model in model.amortization_schedules:
            schedule_entities.append(AmortizationSchedule(
                id=sched_model.id,
                loan_id=sched_model.loan_id,
                installment_number=sched_model.installment_number,
                due_date=sched_model.due_date,
                principal_payment=sched_model.principal_payment,
                interest_payment=sched_model.interest_payment,
                life_insurance=sched_model.life_insurance,
                other_charges=sched_model.other_charges,
                total_installment_amount=sched_model.total_installment_amount,
                principal_balance=sched_model.principal_balance,
                is_paid=sched_model.is_paid
            ))
        loan.amortization_schedule = schedule_entities
        return loan

    def payment_exists(self, payment_reference: str) -> bool:
        from src.infrastructure.adapters.output.persistence.models import PaymentModel
        count = self.session.query(PaymentModel).filter_by(payment_reference=payment_reference).count()
        return count > 0

    def save_payment(self, payment) -> None:
        from src.infrastructure.adapters.output.persistence.models import PaymentModel, PaymentAllocationModel
        payment_model = PaymentModel(
            id=payment.id,
            loan_id=payment.loan_id,
            payment_date=payment.payment_date,
            paid_amount=payment.paid_amount,
            payment_reference=payment.payment_reference,
            payment_method=payment.payment_method.name if hasattr(payment.payment_method, 'name') else payment.payment_method
        )
        self.session.add(payment_model)

        for alloc in payment.allocations:
            alloc_model = PaymentAllocationModel(
                id=alloc.id,
                payment_id=alloc.payment_id,
                amortization_schedule_id=alloc.amortization_schedule_id,
                legal_fees_amount=alloc.legal_fees_amount,
                insurance_amount=alloc.insurance_amount,
                default_interest_amount=alloc.default_interest_amount,
                ordinary_interest_amount=alloc.ordinary_interest_amount,
                principal_amount=alloc.principal_amount
            )
            self.session.add(alloc_model)
