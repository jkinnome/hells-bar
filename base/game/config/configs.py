from base.other.dirs import dirs
from enum import Enum, auto

from rich.console import Console

from base.other.dirs import dirs

CONFIG_DIR = dirs.user_config_path

DISPLAY_FILE = CONFIG_DIR / "display.json"
GAMEPLAY_FILE = CONFIG_DIR / "gameplay.json"
ACCESSIBILITY_FILE = CONFIG_DIR / "accessibility.json"
AUDIO_FILE = CONFIG_DIR / "audio.json"
KEYBINDS_FILE = CONFIG_DIR / "keybinds.json"


class UITheme(Enum):
    Dark = auto()
    Dim = auto()
    Hacker = auto()  # green terminal
    Blood = auto()  # very red
    Custom = auto()  # minimal color picker


color = Console().color_system
font_options: list[float] = [0.8, 1.0, 1.2, 1.5, 2.0]
can_change_tooltips: bool = False
colorblind_options: list[bool | str] = [False, "Deuteranopia", "Protanopia", "Tritanopia"]

DEFAULT_DISPLAY_CONFIG = {
    "corruption_intesity": 0.7,
    "ui_theme": UITheme.Dark.name,
    "color_depth": color,
    "reduce_flicker": False,
    "font_scale": font_options[1]
}

DEFAULT_GAMEPLAY_CONFIG = {
    "confirm_before_drink": True,
    "show_combo_hints": True,
    "tutorial_tooltips": True,
}

DEFAULT_ACCESSIBILITY_CONFIG = {
    "colorblind_mode": colorblind_options[0],
    "screen_reader_mode": False,
    "reduced_corruption": False,
    "high_contrast": False,
    "pause_on_focus_loss": False
}

DEFAULT_AUDIO_CONFIG = {
    "master": 1.0,
    "music": 0.6,
    "ui": 0.5,
    "sfx": 0.7,
    "voice": 0.8
}

DEFAULT_KEYBINDS_CONFIG = {}  # gets handled in another screen and stuff
