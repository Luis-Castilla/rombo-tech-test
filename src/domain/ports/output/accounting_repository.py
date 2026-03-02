from abc import ABC, abstractmethod
from src.domain.entities.accounting import JournalEntry

class IAccountingRepository(ABC):
    @abstractmethod
    def save_journal_entry(self, entry: JournalEntry) -> None:
        pass
