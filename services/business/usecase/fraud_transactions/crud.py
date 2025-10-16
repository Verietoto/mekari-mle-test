from typing import List, Union
from psycopg2.extras import execute_values
from pydantic import TypeAdapter
from ...model.fraud_transactions.fraud_transactions_model import FraudTransactionModel
from ..abc import DatabaseCRUD
from business.domain.supabase.connection import SupabaseDB as DatabaseConnection
from contracts.errors import AppError


class FraudTransactionCRUD(DatabaseCRUD):
    """CRUD operations for the fraud_transactions table."""

    def __init__(self, db: DatabaseConnection):
        if not db:
            raise AppError(status_code=500, code="db_not_initialized", message="Database connection not provided.")
        self.db = db

    # -------------------------------------------
    # Create (supports single or bulk)
    # -------------------------------------------
    def create(self, data: Union[FraudTransactionModel, List[FraudTransactionModel]]) -> int:
        if isinstance(data, FraudTransactionModel):
            data = [data]

        if not data:
            raise AppError(status_code=400, code="empty_payload", message="No transaction data provided.")

        columns = [
            "trans_date_trans_time", "cc_num", "merchant", "category", "amt",
            "first_name", "last_name", "gender", "street", "city", "state", "zip",
            "lat", "long", "city_pop", "job", "dob", "trans_num", "unix_time",
            "merch_lat", "merch_long", "is_fraud"
        ]

        values = [tuple(item.model_dump(by_alias=True).get(col) for col in columns) for item in data]

        query = f"INSERT INTO fraud_transactions ({', '.join(columns)}) VALUES %s"

        try:
            with self.db.get_cursor() as cursor:
                execute_values(cursor, query, values)
                return cursor.rowcount  # Number of rows inserted
        except Exception as e:
            raise AppError(
                status_code=500,
                code="db_insert_failed",
                message=f"Failed to insert transactions: {str(e)}"
            )

    # -------------------------------------------
    #  Read
    # -------------------------------------------
    def read(self, limit: int = 100, **filters) -> List[FraudTransactionModel]:
        query = "SELECT * FROM fraud_transactions"
        params = []

        if filters:
            conditions = [f"{key} = %s" for key in filters.keys()]
            query += " WHERE " + " AND ".join(conditions)
            params.extend(filters.values())

        query += " LIMIT %s"
        params.append(limit)

        with self.db.get_cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

        return TypeAdapter(List[FraudTransactionModel]).validate_python(rows)

    # -------------------------------------------
    # Update
    # -------------------------------------------
    def update(self, identifier: str, data: dict) -> int:
        if not data:
            raise AppError(status_code=400, code="empty_update", message="No data provided for update.")

        set_clause = ', '.join([f"{key} = %s" for key in data.keys()])
        query = f"UPDATE fraud_transactions SET {set_clause} WHERE trans_num = %s;"

        with self.db.get_cursor() as cursor:
            cursor.execute(query, list(data.values()) + [identifier])
            return cursor.rowcount  # Rows updated

    # -------------------------------------------
    # Delete
    # -------------------------------------------
    def delete(self, identifier: str) -> int:
        query = "DELETE FROM fraud_transactions WHERE trans_num = %s;"
        with self.db.get_cursor() as cursor:
            cursor.execute(query, (identifier,),)
            return cursor.rowcount 
