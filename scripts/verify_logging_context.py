import logging

from infra.logging import setup_logging
from infra.request_context import request_id_ctx_var


def verify_logging_context():
    # Setup logging as per application
    setup_logging()
    logger = logging.getLogger("manual_verification")

    # Set a context variable
    test_id = "test-manual-id-999"
    token = request_id_ctx_var.set(test_id)

    # Log something - this should happen in stdout
    # We will capture stdout to verify
    logger.info("This is a test log message with context")

    # Reset token
    request_id_ctx_var.reset(token)

    # Log something without context
    logger.info("This is a test log message WITHOUT context")


if __name__ == "__main__":
    verify_logging_context()
