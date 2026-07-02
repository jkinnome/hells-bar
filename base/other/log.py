import logging
import time
from pathlib import Path

from rich.logging import RichHandler

from dirs import dirs  # platformdirs

"""
btw this is supposed to be like import and use. 
so like i can do from ..log import log and then do log.error("shit")
"""

LOG_NAME = "hells_bar"

LEVEL_COLORS: dict[int, str] = {
    logging.DEBUG: "dim",
    logging.INFO: "white",
    logging.WARNING: "yellow",
    logging.ERROR: "red",
    logging.CRITICAL: "dark_red",
}

_ROTATE_OLD_AFTER = 2 * 24 * 60 * 60  # 2 days till ancient
_ROTATE_DELETE_AFTER = 7 * 24 * 60 * 60  # 7 days till removal


class RichMarkupFomatter(logging.Formatter):
    """Adds a levelcolor field so format can use it"""

    def format(self, record: logging.LogRecord) -> str:
        record.levelcolor = LEVEL_COLORS.get(record.levelno, "white")
        return super().format(record)


FORMAT = r"%(asctime)s | %(module)s - %(funcName)s: [%(levelcolor)s]\[%(levelname)s][/] %(message)s"
PLAIN_FORMAT = "%(asctime)s | %(module)s - %(funcName)s: [%(levelname)s] %(message)s"


def _rotate_logs(directory: Path) -> None:
    """
    Keeps one live hells_bar.log
    < 2 days old -> renamed old_N.log (newest = 1)
    2-7 days old -> renamed ancient_N.log (newest = 1)
    > 7 days old -> deleted
    """
    now = time.time()
    candidates = (
            list(directory.glob(f"{LOG_NAME}.log"))
            + list(directory.glob(f"old_*.log"))
            + list(directory.glob(f"ancient_*.log"))
    )

    old_tier: list[tuple[float, Path]] = []
    ancient_tier: list[tuple[float, Path]] = []

    for path in candidates:
        try:
            mtime = path.stat().st_mtime
        except FileNotFoundError:
            continue

        age = now - mtime
        if age > _ROTATE_DELETE_AFTER:
            path.unlink(missing_ok=True)
        elif age > _ROTATE_OLD_AFTER:
            ancient_tier.append((mtime, path))
        else:
            old_tier.append((mtime, path))

    old_tier.sort(key=lambda t: t[0], reverse=True)
    ancient_tier.sort(key=lambda t: t[0], reverse=True)

    _rename_tier(old_tier, directory, "old")
    _rename_tier(ancient_tier, directory, "ancient")


def _rename_tier(tier: list[tuple[float, Path]], directory: Path, prefix: str) -> None:
    # rename through a temp name first so old_1 and old_2 swaps don't collide
    temp_paths = []
    for i, (_, path) in enumerate(tier):
        temp = directory / f"{prefix}_skibidi_{i}.log"
        path.rename(temp)
        temp_paths.append(temp)

    for i, temp in enumerate(temp_paths, start=1):
        temp.rename(directory / f"{prefix}_{i}.log")


def _get_log_path() -> Path:
    directory = dirs.user_log_path
    directory.mkdir(parents=True, exist_ok=True)
    _rotate_logs(directory)
    return directory / f"{LOG_NAME}.log"


_LOG_PATH = _get_log_path()


def log_rule(label: str | None = None, rule_len: int = 25) -> None:
    label_len = len(label) if label else 0
    rule_amount = max(rule_len - label_len - 4, 0)  # 4 for spaces and |
    rules = "-" * (rule_amount // 2) if rule_amount else ""
    rule = f"{rules}| {label} |{rules}" if label else "-" * rule_len

    with open(_LOG_PATH, "a") as f:
        f.write(rule + "\n")


def get_log() -> logging.Logger:
    return logging.getLogger(__name__)


def get_log_color(levelno: int) -> str:
    return LEVEL_COLORS[levelno]


_file_handler = logging.FileHandler(_LOG_PATH, mode="w", encoding="utf-8")
_file_handler.setFormatter(logging.Formatter(PLAIN_FORMAT, datefmt="[%X]"))

_console_handler = RichHandler(rich_tracebacks=True, markup=True)
_console_handler.setFormatter(RichMarkupFomatter(FORMAT, datefmt="[%X]"))

logging.basicConfig(
    level=logging.DEBUG,  # change this later to error
    handlers=[_file_handler, _console_handler]
)

log = get_log()  # at import time

if __name__ == "__main__":
    log.debug("debug message")
    time.sleep(1)
    log.info("info message")
    time.sleep(1)
    log.warning("warning message")
    time.sleep(1)
    log.error("error message")
    time.sleep(1)
    log.critical("critical message")
    time.sleep(1)
    input("Press any key to exit...")
