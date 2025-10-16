from fastapi import Request
import uuid


async def request_id_middleware(request: Request, call_next):
    """Attach or generate X-Request-Id for every request and return it in response headers."""
    request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    return response
