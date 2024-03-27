import logging


class Logging:
    def __init__(self, level: str = "INFO"):
        assert level in [
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        ], "invalid level: must be one of 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'"

        logging.basicConfig(
            format="%(asctime)s:%(levelname)s: %(message)s",
            level=logging.getLevelName(level),
        )

        self.level = level
        self.logger = logging.getLogger(__name__)

    def get_logger(self):
        return self.logger
