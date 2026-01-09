from contextvars import ContextVar

# Context variable to hold the Request ID
request_id_ctx_var: ContextVar[str | None] = ContextVar("request_id", default=None)
