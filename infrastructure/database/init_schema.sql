CREATE TYPE document_type_enum AS ENUM ('CC', 'CE', 'NIT', 'PASSPORT');
CREATE TYPE portfolio_risk_enum AS ENUM ('A', 'B', 'C', 'D', 'E');
CREATE TYPE loan_status_enum AS ENUM ('SUBMITTED', 'APPROVED', 'DISBURSED', 'CURRENT', 'IN_ARREARS', 'RESTRUCTURED', 'WRITTEN_OFF', 'PAID');
CREATE TYPE payment_modality_enum AS ENUM ('FIXED_INSTALLMENT', 'CONSTANT_PRINCIPAL');
CREATE TYPE interest_rate_type_enum AS ENUM ('EAR', 'NMV'); 
CREATE TYPE payment_method_enum AS ENUM ('PSE', 'BANK_DEPOSIT', 'AUTO_DEBIT', 'BANK_AGENT');
CREATE TYPE account_nature_enum AS ENUM ('DEBIT', 'CREDIT');

CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_type document_type_enum NOT NULL,
    document_number VARCHAR(50) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(150),
    phone_number VARCHAR(20),
    city VARCHAR(100) NOT NULL,
    credit_score INTEGER CHECK (credit_score BETWEEN 0 AND 1000),
    risk_classification portfolio_risk_enum NOT NULL DEFAULT 'A',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (document_type, document_number)
);

CREATE TABLE loans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    requested_amount NUMERIC(18, 2) NOT NULL CHECK (requested_amount > 0),
    approved_amount NUMERIC(18, 2) CHECK (approved_amount > 0),
    interest_rate NUMERIC(10, 6) NOT NULL CHECK (interest_rate >= 0),
    interest_rate_type interest_rate_type_enum NOT NULL,
    term_months INTEGER NOT NULL CHECK (term_months > 0),
    payment_modality payment_modality_enum NOT NULL,
    status loan_status_enum NOT NULL DEFAULT 'SUBMITTED',
    application_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    disbursement_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_loans_customer ON loans(customer_id);
CREATE INDEX idx_loans_status ON loans(status);

CREATE TABLE amortization_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    loan_id UUID NOT NULL REFERENCES loans(id) ON DELETE CASCADE,
    installment_number INTEGER NOT NULL CHECK (installment_number > 0),
    due_date DATE NOT NULL,
    principal_payment NUMERIC(18, 2) NOT NULL DEFAULT 0,
    interest_payment NUMERIC(18, 2) NOT NULL DEFAULT 0,
    life_insurance NUMERIC(18, 2) NOT NULL DEFAULT 0,
    other_charges NUMERIC(18, 2) NOT NULL DEFAULT 0,
    total_installment_amount NUMERIC(18, 2) NOT NULL DEFAULT 0,
    principal_balance NUMERIC(18, 2) NOT NULL DEFAULT 0,
    is_paid BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (loan_id, installment_number)
);
CREATE INDEX idx_amortization_due_date ON amortization_schedules(due_date);

CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    loan_id UUID NOT NULL REFERENCES loans(id) ON DELETE RESTRICT,
    payment_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    paid_amount NUMERIC(18, 2) NOT NULL CHECK (paid_amount > 0),
    payment_reference VARCHAR(100) NOT NULL UNIQUE, 
    payment_method payment_method_enum NOT NULL
);

CREATE TABLE payment_allocations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
    amortization_schedule_id UUID REFERENCES amortization_schedules(id) ON DELETE SET NULL, 
    legal_fees_amount NUMERIC(18, 2) NOT NULL DEFAULT 0,
    insurance_amount NUMERIC(18, 2) NOT NULL DEFAULT 0,
    default_interest_amount NUMERIC(18, 2) NOT NULL DEFAULT 0,
    ordinary_interest_amount NUMERIC(18, 2) NOT NULL DEFAULT 0,
    principal_amount NUMERIC(18, 2) NOT NULL DEFAULT 0
);

CREATE TABLE chart_of_accounts (
    code VARCHAR(20) PRIMARY KEY, 
    name VARCHAR(150) NOT NULL,
    nature account_nature_enum NOT NULL
);

CREATE TABLE journal_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entry_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    description VARCHAR(255) NOT NULL,
    operation_reference UUID 
);

CREATE TABLE journal_entry_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    journal_entry_id UUID NOT NULL REFERENCES journal_entries(id) ON DELETE CASCADE,
    account_code VARCHAR(20) NOT NULL REFERENCES chart_of_accounts(code) ON DELETE RESTRICT,
    debit NUMERIC(18, 2) NOT NULL DEFAULT 0 CHECK (debit >= 0),
    credit NUMERIC(18, 2) NOT NULL DEFAULT 0 CHECK (credit >= 0)
);
