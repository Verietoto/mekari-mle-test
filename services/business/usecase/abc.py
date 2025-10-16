from abc import ABC, abstractmethod
from typing import Any, List

class Usecase(ABC):
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        raise NotImplementedError

class DatabaseCRUD(ABC):
    """Abstract CRUD interface for database operations."""

    @abstractmethod
    def create(self, data: Any) -> Any:
        """Insert a new record into the database."""
        raise NotImplementedError

    @abstractmethod
    def read(self, *args, **kwargs) -> List[Any]:
        """Read records from the database."""
        raise NotImplementedError

    @abstractmethod
    def update(self, identifier: Any, data: Any) -> Any:
        """Update a record in the database."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, identifier: Any) -> Any:
        """Delete a record from the database."""
        raise NotImplementedError
