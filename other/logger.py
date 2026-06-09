"""
LOGGER
PART OF JK'S CUSTOM LIBRARIES

This library exists to very easily log data.

Created by JK
Copyright 2026
"""

import sys
from datetime import datetime

_LEVEL_RANK = {"DEBUG": 0, "INFO": 1, "SUCCESS": 2, "WARN": 3, "ERROR": 4, "CRITICAL": 5}


class Logger:
    """
    Leveled, colored logger that writes to stderr.

    Usage:
        log = Logger(min_level="INFO")
        log.info("Player entered room")
        log.warn("Health below 10%")
        log.error("Save file corrupt")
    """

    def __init__(self,
                 min_level: str = "DEBUG",
                 show_time: bool = True,
                 log_file: str | None = None) -> None:
        self.min_level = min_level
        self.show_time = show_time
        self._log_file = open(log_file, "a") if log_file else None

    def __del__(self) -> None:
        if getattr(self, '_log_file', None):
            # noinspection PyUnresolvedReferences
            self._log_file.close()

    def log(self, message: str, level: str = "INFO") -> None:
        if _LEVEL_RANK.get(level, 0) < _LEVEL_RANK.get(self.min_level, 0):
            return
        timestamp = f"[{datetime.now().strftime('%H:%M:%S')}] " if self.show_time else ""
        tag = f"[{level}]"
        line = f"{timestamp}{tag} {message}"
        sys.stderr.write(line + "\n")
        sys.stderr.flush()
        if self._log_file:
            self._log_file.write(line + "\n")
            self._log_file.flush()

    def section(self, section: str, min_level: str | None = None) -> None:
        """Adds a header to the log to structure the file. Can be disabled with a minimum level."""
        line = f"--------------| {section} |--------------"

        if min_level:
            if _LEVEL_RANK.get(min_level, 0) < _LEVEL_RANK.get(self.min_level, 0):
                return

        sys.stderr.write(line + "\n")
        sys.stderr.flush()
        if self._log_file:
            self._log_file.write(line + "\n")
            self._log_file.flush()

    def debug(self, msg: str) -> None:
        self.log(msg, "DEBUG")

    def info(self, msg: str) -> None:
        self.log(msg, "INFO")

    def success(self, msg: str) -> None:
        self.log(msg, "SUCCESS")

    def warn(self, msg: str) -> None:
        self.log(msg, "WARN")

    def error(self, msg: str) -> None:
        self.log(msg, "ERROR")

    def critical(self, msg: str) -> None:
        self.log(msg, "CRITICAL")

    def close(self) -> None:
        if self._log_file:
            self._log_file.flush()
            self._log_file.close()
