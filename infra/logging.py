import json
import logging
import sys


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "level": record.levelname,
            "message": record.getMessage(),
            "time": self.formatTime(record, self.datefmt),
            "name": record.name,
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        # Inject Request ID if available
        from infra.request_context import request_id_ctx_var

        req_id = request_id_ctx_var.get()
        if req_id:
            log_record["request_id"] = req_id

        return json.dumps(log_record)


def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler])
