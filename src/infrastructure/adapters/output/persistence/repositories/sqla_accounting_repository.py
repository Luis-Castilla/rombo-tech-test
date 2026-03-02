from src.domain.ports.output.accounting_repository import IAccountingRepository
from src.domain.entities.accounting import JournalEntry
from src.infrastructure.adapters.output.persistence.models import JournalEntryModel, JournalEntryLineModel

class SqlAlchemyAccountingRepository(IAccountingRepository):
    def __init__(self, session):
        self.session = session

    def save_journal_entry(self, entry: JournalEntry) -> None:
        journal_model = JournalEntryModel(
            id=entry.id,
            entry_date=entry.entry_date,
            description=entry.description,
            operation_reference=entry.operation_reference
        )
        self.session.add(journal_model)

        for line in entry.lines:
            line_model = JournalEntryLineModel(
                id=line.id,
                journal_entry_id=line.journal_entry_id,
                account_code=line.account_code,
                debit=line.debit,
                credit=line.credit
            )
            self.session.add(line_model)
