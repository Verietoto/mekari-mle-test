from __future__ import annotations
import psycopg2
from psycopg2 import Error as PsycopgError
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Any, Generator, Optional
from ..abc import BaseDatabase
from contracts.errors import AppError


class SupabaseDB(BaseDatabase):
    """Manages connection to the Supabase Postgres database with proper error wrapping."""

    def __init__(self, settings_module: Any):
        # Expecting a module that provides get_settings()
        self.settings = settings_module

    def _get_connection(self) -> psycopg2.extensions.connection:
        """Create a new PostgreSQL database connection."""
        try:
            return psycopg2.connect(
                dbname=self.settings.db_name,
                user=self.settings.db_user,
                password=self.settings.db_password,
                host=self.settings.db_host,
                port=self.settings.db_port,
                cursor_factory=RealDictCursor,
            )
        except PsycopgError as e:
            raise AppError(
                status_code=500,
                code="db_connection_failed",
                message=f"Database connection failed: {e.pgerror or str(e)}",
            )

    @contextmanager
    def get_cursor(self) -> Generator[psycopg2.extensions.cursor, None, None]:
        """Context manager for safely executing DB queries with rollback and AppError wrapping."""
        conn: Optional[psycopg2.extensions.connection] = None
        cursor: Optional[psycopg2.extensions.cursor] = None

        try:
            conn = self._get_connection()
            if conn is None:
                raise AppError(
                    status_code=500,
                    code="db_connection_failed",
                    message="Failed to establish database connection (conn is None).",
                )

            cursor = conn.cursor()
            yield cursor
            conn.commit()

        except PsycopgError as e:
            if conn is not None:
                conn.rollback()
            raise AppError(
                status_code=500,
                code="db_query_failed",
                message=f"Database query failed: {e.pgerror or str(e)}",
            )

        except Exception as e:
            if conn is not None:
                conn.rollback()
            raise AppError(
                status_code=500,
                code="unexpected_db_error",
                message=f"Unexpected database error: {str(e)}",
            )

        finally:
            if cursor is not None:
                cursor.close()
            if conn is not None:
                conn.close()
