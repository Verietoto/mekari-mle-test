from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.security.api_key import APIKeyHeader
from fastapi.encoders import jsonable_encoder
import datetime

from handler.rest.health.health import router as health_router
from handler.rest.fraud_transactions.fraud_transactions import router as fraud_transactions_router
from handler.rest.agentic.agentic import router as agentic_router
from handler.rest.rag.rag import router as rag_router

from contracts.response import ErrorEnvelope, ErrorDetail, Meta
from contracts.errors import AppError
from middleware.request_id import request_id_middleware
from config import get_settings

# -----------------------------------------------------------------------------
# 🔐 Configuration
# -----------------------------------------------------------------------------
API_KEY = get_settings().api_key
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# -----------------------------------------------------------------------------
# 🔐 Dependency: Token Barrier
# -----------------------------------------------------------------------------
async def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "API key"},
        )

# -----------------------------------------------------------------------------
# 🌐 App setup
# -----------------------------------------------------------------------------
app = FastAPI(title="Services API")

app.middleware("http")(request_id_middleware)

# -----------------------------------------------------------------------------
# 🧱 Exception Handler
# -----------------------------------------------------------------------------
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    meta = Meta(
        request_id=getattr(request.state, "request_id", None),
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    )

    payload = ErrorEnvelope(
        error=ErrorDetail(code=exc.code, message=exc.message),
        meta=meta,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(payload),
    )

# -----------------------------------------------------------------------------
# 📦 Routes
# -----------------------------------------------------------------------------
# Protect all routers by default with `Depends(verify_api_key)`
app.include_router(health_router, dependencies=[Depends(verify_api_key)])
app.include_router(fraud_transactions_router, dependencies=[Depends(verify_api_key)])
app.include_router(agentic_router, dependencies=[Depends(verify_api_key)])
app.include_router(rag_router, dependencies=[Depends(verify_api_key)])

# -----------------------------------------------------------------------------
# (Optional) Unprotected root route
# -----------------------------------------------------------------------------
@app.get("/")
async def root():
    return {"message": "Welcome to the Services API"}
