import sys
from pathlib import Path, PurePath
from time import sleep


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
            sys.stdout.write('\033[1A')
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


def change_installation_label(label: str) -> None:
    sys.stdout.write('\033[1A')  # move 1 up
    sys.stdout.write('\r')
    sys.stdout.write('\033[0K')  # clear line
    sys.stdout.write(f"Removing {label}...")
    sys.stdout.write('\033[1B')  # move back down
    sys.stdout.flush()


def unrender_label() -> None:
    sys.stdout.write('\033[1A')
    sys.stdout.write('\r')
    sys.stdout.write('\033[0K')  # clear line
    sys.stdout.flush()
    # stays in same place afterward


def log_error(e: Exception, file: Path) -> None:
    sys.stdout.write('\033[1B')  # move back down
    sys.stdout.write('\r')
    sys.stdout.write(f"\nCould not delete {file.name}: {e}")
    sys.stdout.write('\033[1A')  # move 1 up


def directory_teardown(directory: Path, delete_dir: bool = True) -> None:
    if not directory.is_dir():
        return
    print(f"Deleting all files in {PurePath(directory).name}...")
    print()
    files = list(directory.rglob("*"))
    all_files = [f for f in files if f.is_file()]
    all_dirs = sorted([p for p in files if p.is_dir()], key=lambda p: len(p.parts), reverse=True)
    bar = ProgressBar(len(files))
    bar.render()
    for file in all_files:  # first files
        change_installation_label(str(PurePath(file).name))
        if file.is_file():
            try:
                file.unlink()
            except Exception as e:
                log_error(e, file)
        bar.advance()
    for direct in all_dirs:  # then directories
        change_installation_label(str(PurePath(direct).name))
        if direct.is_dir():
            try:
                direct.rmdir()
            except Exception as e:
                log_error(e, direct)
        bar.advance()

    if delete_dir and list(directory.glob("*")) == []:
        directory.rmdir()
    sleep(1)
    bar.unrender()
    unrender_label()

    print("Done.")
    sleep(1)
    print("\nAll deleted files:")
    sleep(1)
    print("DIRECTORIES:")
    sleep(0.5)
    for d in all_dirs:
        print(PurePath(d).name)
        sleep(0.05)
    sleep(0.5)
    print()
    print("FILES:")
    sleep(0.5)
    for f in all_files:
        print(PurePath(f).name)
        sleep(0.05)
    print()
    sleep(1)
    input("Press enter to exit...")


if __name__ == '__main__':
    direct_test = Path(input("> "))

    sys.stdout.write("\033]2;Data Deleter\007")  # change title
    sys.stdout.write('\033[?25l')  # hide cursor
    sys.stdout.flush()
    try:
        directory_teardown(direct_test)
    finally:
        sys.stdout.write('\033[?25h')  # show cursor before exiting
