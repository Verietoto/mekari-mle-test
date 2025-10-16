import time
from ..abc import Usecase
from ...model.health import HealthModel


class HealthUsecase(Usecase):
    def __init__(self) -> None:
        self._start_time = time.time()

    def execute(self) -> HealthModel:
        uptime = time.time() - self._start_time
        return HealthModel(status="ok", uptime_seconds=round(uptime, 2))
