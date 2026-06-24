import importlib.util
import subprocess
import sys
from time import sleep
from pathlib import Path

required: Path = Path(__file__).resolve().parent.parent / "requirements.txt"


def populate() -> list[str]:
    libraries: list[str] = []
    with open(required) as f:
        for lines in f.readlines():
            line = lines.strip()
            if line:
                libraries.append(line)
    return libraries

class ProgressBar:
    def __init__(self, total: int, width: int = 30, fill: str = '█',
                 empty: str = '░', prefix: str = '') -> None:
        self.total = total
        self.current = 0
        self.width = width
        self.fill = fill
        self.empty = empty
        self.prefix = prefix

    def advance(self, amount: int = 1, include_render: bool = True) -> None:
        self.current = min(self.current + amount, self.total)
        if include_render:
            self.render()

    def reset(self) -> None:
        self.current = 0

    def render(self) -> None:
        pct = self.current / self.total if self.total > 0 else 1.0
        filled = int(self.width * pct)
        full_bar = self.fill * filled + self.empty * (self.width - filled)
        sys.stdout.write(f"\r{self.prefix} [{full_bar}] {int(pct * 100)}%")
        sys.stdout.flush()
        if self.current >= self.total:
            print()


def teardown(installed: list[str]) -> None:
    if installed:
        print(f"Uninstalling {', '.join(installed)}...")
        bar: ProgressBar = ProgressBar(len(installed))
        for package in installed:
            subprocess.check_call(
                # fine if package doesn't exist/isn't installed
                [sys.executable, "-m", "pip", "uninstall", package, "-y"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            bar.advance()
        print("Done.")
    else:
        print("None of the listed packages are currently installed.")

    sleep(1)
    print()
    print("Exiting...")
    sleep(2)


if __name__ == "__main__":
    REQUIRED = populate()
    sys.stdout.write("\033]2;uninstaller\007")  # change title
    sys.stdout.write('\033[?25l')  # hide cursor
    sys.stdout.flush()
    try:
        teardown(REQUIRED)
    finally:
        sys.stdout.write('\033[?25h')  # show cursor before exiting
