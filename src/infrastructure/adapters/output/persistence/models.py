import uuid
import enum
from sqlalchemy.dialects.postgresql import UUID
from src.infrastructure.config.extensions import db

class DocumentTypeEnum(enum.Enum):
    CC = 'CC'
    CE = 'CE'
    NIT = 'NIT'
    PASSPORT = 'PASSPORT'

class PortfolioRiskEnum(enum.Enum):
    A = 'A'
    B = 'B'
    C = 'C'
    D = 'D'
    E = 'E'

class LoanStatusEnum(enum.Enum):
    SUBMITTED = 'SUBMITTED'
    APPROVED = 'APPROVED'
    DISBURSED = 'DISBURSED'
    CURRENT = 'CURRENT'
    IN_ARREARS = 'IN_ARREARS'
    RESTRUCTURED = 'RESTRUCTURED'
    WRITTEN_OFF = 'WRITTEN_OFF'
    PAID = 'PAID'

class PaymentModalityEnum(enum.Enum):
    FIXED_INSTALLMENT = 'FIXED_INSTALLMENT'
    CONSTANT_PRINCIPAL = 'CONSTANT_PRINCIPAL'

class InterestRateTypeEnum(enum.Enum):
    EAR = 'EAR'
    NMV = 'NMV'

class PaymentMethodEnum(enum.Enum):
    PSE = 'PSE'
    BANK_DEPOSIT = 'BANK_DEPOSIT'
    AUTO_DEBIT = 'AUTO_DEBIT'
    BANK_AGENT = 'BANK_AGENT'

class AccountNatureEnum(enum.Enum):
    DEBIT = 'DEBIT'
    CREDIT = 'CREDIT'


class CustomerModel(db.Model):
    __tablename__ = 'customers'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_type = db.Column(db.Enum(DocumentTypeEnum, name='document_type_enum'), nullable=False)
    document_number = db.Column(db.String(50), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150))
    phone_number = db.Column(db.String(20))
    city = db.Column(db.String(100), nullable=False)
    credit_score = db.Column(db.Integer)
    borrowing_capacity = db.Column(db.Numeric(18,2), nullable=False, default=0)
    risk_classification = db.Column(db.Enum(PortfolioRiskEnum, name='portfolio_risk_enum'), nullable=False, default=PortfolioRiskEnum.A)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    loans = db.relationship('LoanModel', backref='customer', lazy=True)
    __table_args__ = (
        db.UniqueConstraint('document_type', 'document_number', name='uq_customer_document'),
        db.CheckConstraint('credit_score BETWEEN 0 AND 1000', name='chk_customer_credit_score')
    )


class LoanModel(db.Model):
    __tablename__ = 'loans'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('customers.id', ondelete='RESTRICT'), nullable=False, index=True)
    requested_amount = db.Column(db.Numeric(18, 2), nullable=False)
    approved_amount = db.Column(db.Numeric(18, 2))
    interest_rate = db.Column(db.Numeric(10, 6), nullable=False)
    interest_rate_type = db.Column(db.Enum(InterestRateTypeEnum, name='interest_rate_type_enum'), nullable=False)
    term_months = db.Column(db.Integer, nullable=False)
    payment_modality = db.Column(db.Enum(PaymentModalityEnum, name='payment_modality_enum'), nullable=False)
    status = db.Column(db.Enum(LoanStatusEnum, name='loan_status_enum'), nullable=False, default=LoanStatusEnum.SUBMITTED, index=True)
    application_date = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    disbursement_date = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    amortization_schedules = db.relationship('AmortizationScheduleModel', backref='loan', lazy=True, cascade="all, delete-orphan")
    payments = db.relationship('PaymentModel', backref='loan', lazy=True)

    __table_args__ = (
        db.CheckConstraint('requested_amount > 0', name='chk_loans_requested_amount'),
        db.CheckConstraint('approved_amount > 0', name='chk_loans_approved_amount'),
        db.CheckConstraint('interest_rate >= 0', name='chk_loans_interest_rate'),
        db.CheckConstraint('term_months > 0', name='chk_loans_term_months'),
    )


class AmortizationScheduleModel(db.Model):
    __tablename__ = 'amortization_schedules'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loan_id = db.Column(UUID(as_uuid=True), db.ForeignKey('loans.id', ondelete='CASCADE'), nullable=False)
    installment_number = db.Column(db.Integer, nullable=False)
    due_date = db.Column(db.Date, nullable=False, index=True)
    principal_payment = db.Column(db.Numeric(18, 2), nullable=False, default=0)
    interest_payment = db.Column(db.Numeric(18, 2), nullable=False, default=0)
    life_insurance = db.Column(db.Numeric(18, 2), nullable=False, default=0)
    other_charges = db.Column(db.Numeric(18, 2), nullable=False, default=0)
    total_installment_amount = db.Column(db.Numeric(18, 2), nullable=False, default=0)
    principal_balance = db.Column(db.Numeric(18, 2), nullable=False, default=0)
    is_paid = db.Column(db.Boolean, nullable=False, default=False)

    __table_args__ = (
        db.UniqueConstraint('loan_id', 'installment_number', name='uq_loan_installment'),
        db.CheckConstraint('installment_number > 0', name='chk_amortization_installment_number')
    )


class PaymentModel(db.Model):
    __tablename__ = 'payments'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loan_id = db.Column(UUID(as_uuid=True), db.ForeignKey('loans.id', ondelete='RESTRICT'), nullable=False)
    payment_date = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    paid_amount = db.Column(db.Numeric(18, 2), nullable=False)
    payment_reference = db.Column(db.String(100), nullable=False, unique=True)
    payment_method = db.Column(db.Enum(PaymentMethodEnum, name='payment_method_enum'), nullable=False)

    allocations = db.relationship('PaymentAllocationModel', backref='payment', lazy=True, cascade="all, delete-orphan")

    __table_args__ = (
        db.CheckConstraint('paid_amount > 0', name='chk_payments_paid_amount'),
    )


class PaymentAllocationModel(db.Model):
    __tablename__ = 'payment_allocations'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = db.Column(UUID(as_uuid=True), db.ForeignKey('payments.id', ondelete='CASCADE'), nullable=False)
    amortization_schedule_id = db.Column(UUID(as_uuid=True), db.ForeignKey('amortization_schedules.id', ondelete='SET NULL'))
    legal_fees_amount = db.Column(db.Numeric(18, 2), nullable=False, default=0)
    insurance_amount = db.Column(db.Numeric(18, 2), nullable=False, default=0)
    default_interest_amount = db.Column(db.Numeric(18, 2), nullable=False, default=0)
    ordinary_interest_amount = db.Column(db.Numeric(18, 2), nullable=False, default=0)
    principal_amount = db.Column(db.Numeric(18, 2), nullable=False, default=0)


class ChartOfAccountModel(db.Model):
    __tablename__ = 'chart_of_accounts'

    code = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    nature = db.Column(db.Enum(AccountNatureEnum, name='account_nature_enum'), nullable=False)


class JournalEntryModel(db.Model):
    __tablename__ = 'journal_entries'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entry_date = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    operation_reference = db.Column(UUID(as_uuid=True))

    lines = db.relationship('JournalEntryLineModel', backref='journal_entry', lazy=True, cascade="all, delete-orphan")


class JournalEntryLineModel(db.Model):
    __tablename__ = 'journal_entry_lines'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    journal_entry_id = db.Column(UUID(as_uuid=True), db.ForeignKey('journal_entries.id', ondelete='CASCADE'), nullable=False)
    account_code = db.Column(db.String(20), db.ForeignKey('chart_of_accounts.code', ondelete='RESTRICT'), nullable=False)
    debit = db.Column(db.Numeric(18, 2), nullable=False, default=0)
    credit = db.Column(db.Numeric(18, 2), nullable=False, default=0)

    __table_args__ = (
        db.CheckConstraint('debit >= 0', name='chk_journal_debit'),
        db.CheckConstraint('credit >= 0', name='chk_journal_credit')
    )