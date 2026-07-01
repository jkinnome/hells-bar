import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dirs import dirs


def _get_log_path() -> str:
    directory = dirs.user_log_path
    filename = "hell's-bar.log"
    count = 0
    while True:
        full = directory / filename
        if full.exists():
            filename = f"hell's-bar_{count}.log"
            count += 1
        else:
            break

    return full


def log_rule(label: str | None = None, rule_len: int = 25) -> None:
    path = _get_log_path()
    label_len = len(label) if label else 0
    rule_amount = max(rule_len - label_len - 2, 0)  # 2 for spaces
    rules = "-" * (rule_amount // 2) if rule_amount else ""
    rule = f"{rules} {label} {rules}" if label else "-" * rule_len

    with open(path, "a") as f:
        f.write(rule)


log = logging.basicConfig(
    filename=_get_log_path(),
    filemode="w",
    format='%(asctime)s | %(module)s - %(funcName)s: [%(levelname)s] %(message)s',
    level=logging.DEBUG
)
