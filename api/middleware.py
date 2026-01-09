import json
import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from infra.request_context import request_id_ctx_var

logger = logging.getLogger("api.middleware")


class TraceIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Set ContextVar and Request State
        token = request_id_ctx_var.set(request_id)
        request.state.request_id = request_id

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            request_id_ctx_var.reset(token)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000

            log_data = {
                "message": "Request processed",
                "path": request.url.path,
                "method": request.method,
                "status_code": response.status_code,
                "duration_ms": round(process_time, 2),
                # request_id is now automatically added by the formatter via ContextVar
                # we can keep it here for redundancy or remove it.
                # Let's keep it in the message object for direct readability in this specific log.
                "request_id": request_id_ctx_var.get(),
            }
            logger.info(json.dumps(log_data))

            return response
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            log_data = {
                "message": "Request failed",
                "path": request.url.path,
                "method": request.method,
                "duration_ms": round(process_time, 2),
                "request_id": request_id_ctx_var.get(),
                "error": str(e),
            }
            logger.error(json.dumps(log_data))
            raise e
