from fastapi import APIRouter, Depends, status
from typing import List, Union
import time
from business.usecase.fraud_transactions.crud import FraudTransactionCRUD
from business.model.fraud_transactions.fraud_transactions_model import FraudTransactionModel
from business.domain.supabase.connection import SupabaseDB
from contracts.response import SuccessEnvelope
from config import get_settings

router = APIRouter(prefix="/fraud/v1/transactions", tags=["Fraud Transactions"])


# ================= Dependency Injection =================
def get_crud() -> FraudTransactionCRUD:
    """Provide a CRUD instance with a Supabase DB connection."""
    settings = get_settings()
    db = SupabaseDB(settings)
    return FraudTransactionCRUD(db=db)


# ================== Handler ==================
class FraudTransactionHandler:
    def __init__(self, crud):
        self._crud = crud
    
    def get(self, limit: int = 100) -> List[FraudTransactionModel]:
        return self._crud.read(limit=limit)
    
    def create(self, data: Union[FraudTransactionModel, list]):
        start_time = time.perf_counter()
        rows_affected = self._crud.create(data)
        duration_ms = (time.perf_counter() - start_time) * 1000
        return {"rows_affected": rows_affected, "duration_ms": round(duration_ms, 2)}

    def update(self, trans_num: str, data: dict):
        start_time = time.perf_counter()
        rows_affected = self._crud.update(trans_num, data)
        duration_ms = (time.perf_counter() - start_time) * 1000
        return {"rows_affected": rows_affected, "duration_ms": round(duration_ms, 2)}

    def delete(self, trans_num: str):
        start_time = time.perf_counter()
        rows_affected = self._crud.delete(trans_num)
        duration_ms = (time.perf_counter() - start_time) * 1000
        return {"rows_affected": rows_affected, "duration_ms": round(duration_ms, 2)}

# ================== Endpoints ==================
@router.get("/", response_model=SuccessEnvelope[List[FraudTransactionModel]])
async def list_transactions(
    limit: int = 100,
    crud: FraudTransactionCRUD = Depends(get_crud)
):
    handler = FraudTransactionHandler(crud)
    result = handler.get(limit=limit)
    return SuccessEnvelope[List[FraudTransactionModel]](data=result)


@router.post("/", response_model=SuccessEnvelope[dict], status_code=status.HTTP_201_CREATED)
async def create_transaction(
    models: List[FraudTransactionModel],
    crud: FraudTransactionCRUD = Depends(get_crud)
):
    handler = FraudTransactionHandler(crud)
    result = handler.create(models)
    return SuccessEnvelope[dict](data=result)


@router.put("/{trans_num}", response_model=SuccessEnvelope[str])
async def update_transaction(
    trans_num: str,
    data: dict,
    crud: FraudTransactionCRUD = Depends(get_crud)
):
    handler = FraudTransactionHandler(crud)
    handler.update(trans_num, data)
    return SuccessEnvelope[str](data="Transaction updated successfully")


@router.delete("/{trans_num}", response_model=SuccessEnvelope[str])
async def delete_transaction(
    trans_num: str,
    crud: FraudTransactionCRUD = Depends(get_crud)
):
    handler = FraudTransactionHandler(crud)
    handler.delete(trans_num)
    return SuccessEnvelope[str](data="Transaction deleted successfully")
