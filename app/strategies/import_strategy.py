
from abc import ABC, abstractmethod


class ImportStrategy(ABC):

    @abstractmethod
    def validate(self, row):
        """Validate an individual imported record."""
        pass

    @abstractmethod
    def import_data(self, row):
        """Convert a valid row into application data."""
        pass
