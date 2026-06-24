"""
PACKAGESETUP
PART OF JK'S CUSTOM LIBRARIES

This library exists to allow the user to automatically install all required external libraries

Created by JK
Copyright 2026
"""

"""edited for Hell's Bar. Included bars from consolecontroller"""

import importlib.util
import subprocess
import sys
import threading
from time import sleep

DIF_REQUIREMENT: dict[str, str] = {
    "pygame": "pygame-ce",
}

REQUIREMENTS: dict[str, str] = {}


def populate_requirements(requirements: dict[str, str],
                          dif_requirements: dict[str, str]) -> dict[str, str]:
    try:
        with open("requirements.txt", "r") as f:
            for lines in f.readlines():
                line = lines.strip()
                if line:
                    requirements[line] = line  # populates dict: "rich": "rich"
        for imp, pip in dif_requirements.items():  # changes dict depending on dif import name
            if pip in requirements:
                requirements[imp] = requirements.pop(pip)
    except FileNotFoundError as e:
        sys.stderr.write(f"CRITICAL ERROR: {e}\n"
                         "TRY REINSTALLING REQUIREMENTS.TXT OFF OF THE GITHUB PAGE\n")

    return requirements


def change_installation_label(label: str) -> None:
    sys.stdout.write('\033[1A')  # move 1 up
    sys.stdout.write('\r')
    sys.stdout.write('\033[0K')  # clear line
    sys.stdout.write(f"Installing {label}...")
    sys.stdout.write('\033[1B')  # move back down
    sys.stdout.flush()


def unrender_label() -> None:
    sys.stdout.write('\033[1A')
    sys.stdout.write('\r')
    sys.stdout.write('\033[0K')  # clear line
    sys.stdout.flush()
    # stays in same place afterward


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

    @staticmethod
    def unrender(go_up: bool = True) -> None:
        if go_up:
            sys.stdout.write(f'\033[1A')
            sys.stdout.flush()
        sys.stdout.write('\r' + "\033[0K" + '\r')
        sys.stdout.flush()

    def render(self) -> None:
        pct = self.current / self.total if self.total > 0 else 1.0
        filled = int(self.width * pct)
        full_bar = self.fill * filled + self.empty * (self.width - filled)
        sys.stdout.write(f"\r{full_bar} {int(pct * 100)}%")
        sys.stdout.flush()
        if self.current >= self.total:
            print()


class LoadingBar:
    def __init__(self, width: int = 30, highlight_size: int = 8, speed: float = 0.05, label: str = '', empty: str = '░',
                 fill: str = '█'):
        self.width = width
        self.fill = fill
        self.empty = empty
        self.highlight_size = highlight_size
        self.speed = speed
        self.label = f' {label}' if label else ''
        self._stop_event = threading.Event()
        self._thread = None

    def _animate(self):
        pos = 0
        while not self._stop_event.is_set():
            bar = [self.empty] * self.width
            for i in range(self.highlight_size):
                bar[(pos + i) % self.width] = self.fill

            sys.stdout.write(f'\r{"".join(bar)}{self.label}')
            sys.stdout.flush()

            pos = (pos + 1) % self.width
            sleep(self.speed)

    def start(self):
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join()
        # Clear the line so it doesn't leave a ghost bar behind
        sys.stdout.write('\r' + ' ' * (self.width + 2 + len(self.label)) + '\r')
        sys.stdout.flush()

    # Context manager support
    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False  # don't suppress exceptions


# --- Usage ---
def setup(required: dict[str, str], bar_fill: str = "█", bar_empty: str = "░") -> None:
    print("Upgrading PIP...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "--upgrade", "pip", "--quiet"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    sleep(1)
    print("Done.")
    sleep(1)
    print("\nSearching for missing packages...")

    with LoadingBar(fill=bar_fill, empty=bar_empty, label='Searching...'):
        missing = [
            pip_name
            for import_name, pip_name in required.items()
            if importlib.util.find_spec(import_name) is None
        ]
        sleep(3)

    sleep(1)
    if missing:
        bar: ProgressBar = ProgressBar(total=len(missing), fill=bar_fill, empty=bar_empty)
        bar.render()
        for calls in missing:
            change_installation_label(calls)
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", calls],
                stdout=subprocess.DEVNULL,  # hide noisy pip output
                stderr=subprocess.DEVNULL
            )
            bar.advance()
        sleep(1)
        bar.unrender()
        unrender_label()
        print("Installing...")  # empty label
        print("Done.")
    else:
        print("All packages are already installed.")

    sleep(1)
    print()
    print("Exiting...")
    sleep(2)


if __name__ == "__main__":
    REQUIREMENTS = populate_requirements(REQUIREMENTS, DIF_REQUIREMENT)
    sys.stdout.write("\033]2;Hell's Bar: SETUP\007")  # change title
    sys.stdout.write('\033[?25l')  # hide cursor
    sys.stdout.flush()
    try:
        setup(REQUIREMENTS, "♥", "♡")
    finally:
        sys.stdout.write('\033[?25h')  # show cursor before exiting
