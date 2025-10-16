from __future__ import annotations
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Generator, Optional


class BaseDatabase(ABC):
    """Abstract base class for database connections."""

    def __init__(self, settings_module: Any):
        # Expecting a module or object that provides get_settings()
        self.settings = settings_module.get_settings()

    @abstractmethod
    def _get_connection(self) -> Any:
        """Return a new database connection object."""
        raise NotImplementedError

    @contextmanager
    def get_cursor(self) -> Generator[Any, None, None]:
        """Context manager for safely executing queries."""
        conn: Optional[Any] = None
        cursor: Optional[Any] = None

        try:
            conn = self._get_connection()
            if conn is None:
                raise ConnectionError("Database connection failed (None returned).")

            cursor = conn.cursor()
            yield cursor
            conn.commit()

        except Exception:
            if conn is not None:
                conn.rollback()
            raise

        finally:
            if cursor is not None:
                cursor.close()
            if conn is not None:
                conn.close()
