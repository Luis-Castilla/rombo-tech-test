from decimal import Decimal
from typing import List
from datetime import datetime, timezone
import uuid
from src.domain.entities.accounting import JournalEntry, JournalEntryLine
from src.domain.entities.enums import ColombianPUCEnum

class AccountingFactory:
    """
    Domain factory to generate standard accounting double-entry (Partida Doble) journals based on operations.
    """
    
    @staticmethod
    def create_loan_disbursement_journal(loan_id: uuid.UUID, amount: Decimal) -> JournalEntry:
        """
        Creates a JournalEntry for loan disbursement.
        Debit: 1405 (Cartera de Créditos)
        Credit: 1110 (Bancos)
        """
        entry_id = uuid.uuid4()
        
        lines = [
            JournalEntryLine(
                journal_entry_id=entry_id,
                account_code=ColombianPUCEnum.CARTERA_CREDITOS.value,
                debit=amount,
                credit=Decimal('0.00'),
                id=uuid.uuid4()
            ),
            JournalEntryLine(
                journal_entry_id=entry_id,
                account_code=ColombianPUCEnum.BANCOS.value,
                debit=Decimal('0.00'),
                credit=amount,
                id=uuid.uuid4()
            )
        ]
        
        return JournalEntry(
            id=entry_id,
            description=f"Disbursement for Loan {loan_id}",
            entry_date=datetime.now(timezone.utc),
            operation_reference=loan_id,
            lines=lines
        )

    @staticmethod
    def create_loan_payment_journal(loan_id: uuid.UUID, payment_id: uuid.UUID, total_amount: Decimal, 
                                    principal: Decimal, interest: Decimal, insurance: Decimal) -> JournalEntry:
        """
        Creates a JournalEntry for loan payment collection.
        Debit: 1110 (Bancos) - Total
        Credit: 1405 (Cartera/Capital), 4150 (Ingresos Intereses), 2335 (Cuentas por pagar Seguros)
        """
        entry_id = uuid.uuid4()
        lines = []

        # Debit to Bank -> Total cash received
        lines.append(JournalEntryLine(
            journal_entry_id=entry_id, account_code=ColombianPUCEnum.BANCOS.value,
            debit=total_amount, credit=Decimal('0.00'), id=uuid.uuid4()
        ))

        if principal > Decimal('0'):
            lines.append(JournalEntryLine(
                journal_entry_id=entry_id, account_code=ColombianPUCEnum.CARTERA_CREDITOS.value,
                debit=Decimal('0.00'), credit=principal, id=uuid.uuid4()
            ))
            
        if interest > Decimal('0'):
            lines.append(JournalEntryLine(
                journal_entry_id=entry_id, account_code=ColombianPUCEnum.INGRESOS_INTERESES.value,
                debit=Decimal('0.00'), credit=interest, id=uuid.uuid4()
            ))

        if insurance > Decimal('0'):
            lines.append(JournalEntryLine(
                journal_entry_id=entry_id, account_code=ColombianPUCEnum.CUENTAS_POR_PAGAR_SEGUROS.value,
                debit=Decimal('0.00'), credit=insurance, id=uuid.uuid4()
            ))

        return JournalEntry(
            id=entry_id,
            description=f"Payment Collection for Loan {loan_id}",
            entry_date=datetime.now(timezone.utc),
            operation_reference=payment_id,
            lines=lines
        )
