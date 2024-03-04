from loguru import logger


class BadRequest(Exception):
    def __init__(self, message: str):
        logger.trace(f"BadRequest exception message: {message}")

        self.message = message
        super(BadRequest, self).__init__(message)
