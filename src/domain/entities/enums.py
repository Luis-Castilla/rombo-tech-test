from enum import Enum

class DocumentTypeEnum(Enum):
    CC = 'CC'
    CE = 'CE'
    NIT = 'NIT'
    PASSPORT = 'PASSPORT'

class PortfolioRiskEnum(Enum):
    A = 'A'
    B = 'B'
    C = 'C'
    D = 'D'
    E = 'E'

class LoanStatusEnum(Enum):
    SUBMITTED = 'SUBMITTED'
    APPROVED = 'APPROVED'
    DISBURSED = 'DISBURSED'
    CURRENT = 'CURRENT'
    IN_ARREARS = 'IN_ARREARS'
    RESTRUCTURED = 'RESTRUCTURED'
    WRITTEN_OFF = 'WRITTEN_OFF'
    PAID = 'PAID'

class PaymentModalityEnum(Enum):
    FIXED_INSTALLMENT = 'FIXED_INSTALLMENT'
    CONSTANT_PRINCIPAL = 'CONSTANT_PRINCIPAL'

class InterestRateTypeEnum(Enum):
    EAR = 'EAR'
    NMV = 'NMV'

class PaymentMethodEnum(Enum):
    PSE = 'PSE'
    BANK_DEPOSIT = 'BANK_DEPOSIT'
    AUTO_DEBIT = 'AUTO_DEBIT'
    BANK_AGENT = 'BANK_AGENT'

class AccountNatureEnum(Enum):
    DEBIT = 'DEBIT'
    CREDIT = 'CREDIT'

class ColombianPUCEnum(Enum):
    BANCOS = '1110'
    CARTERA_CREDITOS = '1405'
    CUENTAS_POR_PAGAR_SEGUROS = '2335'
    INGRESOS_INTERESES = '4150'
