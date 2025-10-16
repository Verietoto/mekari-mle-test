from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import datetime

from handler.rest.health.health import router as health_router
from handler.rest.fraud_transactions.fraud_transactions import router as fraud_transactions_router
from handler.rest.agentic.agentic import router as agentic_router
from handler.rest.rag.rag import router as rag_router
from contracts.response import ErrorEnvelope, ErrorDetail, Meta
from contracts.errors import AppError
from middleware.request_id import request_id_middleware
from fastapi.encoders import jsonable_encoder

app = FastAPI(title="Services API")


app.middleware("http")(request_id_middleware)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    meta = Meta(
        request_id=getattr(request.state, "request_id", None),
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )

    payload = ErrorEnvelope(
        error=ErrorDetail(code=exc.code, message=exc.message),
        meta=meta
    )

    # ✅ Convert to fully JSON-safe types (e.g. datetime → str)
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(payload)
    )


app.include_router(health_router)
app.include_router(fraud_transactions_router)
app.include_router(agentic_router)
app.include_router(rag_router)
