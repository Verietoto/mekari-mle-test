from fastapi import APIRouter, Request

from business.usecase.health.health_usecase import HealthUsecase
from contracts.response import SuccessEnvelope
from business.model.health import HealthModel

router = APIRouter(prefix="/health/v1")


class HealthHandler:

    def __init__(self, usecase: HealthUsecase) -> None:
        self._usecase = usecase

    def handle(self, request: Request) -> HealthModel:
        # No request data needed for health; call usecase
        return self._usecase.execute()

default_usecase = HealthUsecase()
default_handler = HealthHandler(default_usecase)


# ============== Health Check ==============
# Health check endpoint (liveness & uptime)
# Route: GET /health/v1/check
@router.get("/check", response_model=SuccessEnvelope[HealthModel])
async def health_endpoint(request: Request):
    result = default_handler.handle(request)
    return SuccessEnvelope[HealthModel](data=result)
