"""
directory_guard.py — Point 4: Mod Directory Separation
=======================================================
Enforces a hard physical separation between protected base game content
and user-installed mods.  The rules are simple and absolute:

  base/   Read-only.  Contains shipped game assets.  Mods may never
          write here.  The game's update/launcher system is the only
          thing that should ever unlock it.

  mods/   Writable by the user.  Each subdirectory is one mod.
          Nothing in mods/ is ever merged into base/.

The VFS resolution (finding the right file at runtime) lives in
mod_loader.py where load priority is respected.  This module only
handles the physical directory layout and safety enforcement.
"""

import os
import stat
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
# Exceptions
# ─────────────────────────────────────────────────────────────────────────────

class DirectoryViolation(Exception):
    """
    Raised when a mod contains files that would land inside the protected
    base/ directory, or when a path-traversal attack is detected.
    """


# ─────────────────────────────────────────────────────────────────────────────
# Main guard class
# ─────────────────────────────────────────────────────────────────────────────

class GameDirectoryGuard:
    """
    Manages the physical directory layout and enforces the base/mods split.

    Expected layout under game_root:
        game_root/
        ├── base/       <- protected; read-only after initial setup
        │   ├── manifest.json
        │   ├── manifest.sig   (if using signing)
        │   └── ...           (actual game assets)
        └── mods/       <- one subdirectory per installed mod
            ├── my_cool_mod/
            │   ├── mod.json
            │   └── ...
            └── another_mod/
                ├── mod.json
                └── ...
    """

    def __init__(self, game_root: Path) -> None:
        # Resolve to absolute path so is_base_path / is_mod_path comparisons
        # are not fooled by relative ".." traversal
        self.game_root = Path(game_root).resolve()
        self.base_dir = self.game_root / "base"
        self.mods_dir = self.game_root / "mods"

    # ─────────────────────────────────────────
    # Directory lifecycle
    # ─────────────────────────────────────────

    def ensure_structure(self) -> None:
        """
        Create base/ and mods/ if they don't exist.
        Safe to call on every startup — does nothing if already present.
        """
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.mods_dir.mkdir(parents=True, exist_ok=True)
        print(f"Directory structure verified under {self.game_root}")

    def lock_base_directory(self) -> None:
        """
        Recursively set base/ and all its contents to read-only at the OS level.

        This means:
          - Any accidental write (even from a file manager or rogue script)
            raises PermissionError immediately.
          - A mod that somehow got a path into base/ will fail loudly on
            the write attempt, not silently corrupt the file.

        Call this after every game update and on first setup.
        """
        self._chmod_tree(self.base_dir, write=False)
        print(f"base/ locked read-only: {self.base_dir}")

    def unlock_base_directory(self) -> None:
        """
        Restore write permissions on base/ for the game's update system.
        Should only ever be called from your launcher/updater, never from
        game logic or mod-facing code.

        Always pair with lock_base_directory() in a try/finally:

            guard.unlock_base_directory()
            try:
                perform_update()
            finally:
                guard.lock_base_directory()
        """
        self._chmod_tree(self.base_dir, write=True)
        print(f"base/ unlocked (remember to re-lock after update): {self.base_dir}")

    @staticmethod
    def _chmod_tree(root: Path, *, write: bool) -> None:
        """Recursively add or strip the write bit on a directory tree."""
        targets = [root, *root.rglob("*")]
        for path in targets:
            current = path.stat().st_mode
            if write:
                # Restore owner-write
                new_mode = current | stat.S_IWRITE
            else:
                # Remove write bits for owner, group, and others
                new_mode = current & ~(stat.S_IWRITE | stat.S_IWGRP | stat.S_IWOTH)
            path.chmod(new_mode)

    # ─────────────────────────────────────────
    # Path classification
    # ─────────────────────────────────────────

    def is_base_path(self, path: Path) -> bool:
        """
        Return True if the given path (after symlink resolution) lives
        inside base/.  Used to detect path-traversal attacks.
        """
        try:
            Path(path).resolve().relative_to(self.base_dir)
            return True
        except ValueError:
            return False

    def is_mod_path(self, path: Path) -> bool:
        """Return True if the given path lives inside mods/."""
        try:
            Path(path).resolve().relative_to(self.mods_dir)
            return True
        except ValueError:
            return False

    def which_mod(self, path: Path) -> str | None:
        """
        If the path is inside mods/, return the mod's directory name.
        Returns None if it's not a mod path.

        Example: mods/cool_mod/sprites/goblin.png → "cool_mod"
        """
        try:
            rel = Path(path).resolve().relative_to(self.mods_dir)
            return rel.parts[0] if rel.parts else None
        except ValueError:
            return None

    # ─────────────────────────────────────────
    # Mod installation safety check
    # ─────────────────────────────────────────

    def validate_mod_files(self, mod_source_dir: Path) -> list[str]:
        """
        Inspect every file in mod_source_dir and ensure none would end up
        inside base/ after installation.  Protects against:

          - Deliberate path-traversal attacks (e.g. "../../base/data.json")
          - Naive mod tools that accidentally produce absolute paths

        Args:
            mod_source_dir: The directory containing the unpacked mod.

        Returns:
            A list of relative POSIX paths that are safe to install.

        Raises:
            DirectoryViolation: If any file would land inside base/.
        """
        mod_source_dir = Path(mod_source_dir).resolve()
        safe = []
        violations = []

        for file_path in mod_source_dir.rglob("*"):
            if not file_path.is_file():
                continue

            rel = file_path.relative_to(mod_source_dir).as_posix()

            # Reconstruct where this file would land after install.
            # If that destination is inside base/, it's a violation.
            install_target = (self.mods_dir / mod_source_dir.name / rel).resolve()
            if self.is_base_path(install_target):
                violations.append(rel)
            else:
                safe.append(rel)

        if violations:
            raise DirectoryViolation(
                f"Mod '{mod_source_dir.name}' contains files targeting the "
                f"protected base/ directory:\n"
                + "\n".join(f"  x {v}" for v in violations)
            )

        return safe

    # ─────────────────────────────────────────
    # Simple mod-first path resolution
    # ─────────────────────────────────────────

    def resolve(self, logical_path: str) -> Path | None:
        """
        Resolve a logical game asset path to a real file on disk.

        Checks every mod directory first (in filesystem order — for
        proper priority ordering, use ModLoader.resolve() from mod_loader.py
        which respects load_priority).  Falls back to base/ if no mod
        provides the file.

        Args:
            logical_path: A path relative to the game root, e.g.
                          "sprites/enemies/goblin.png" or "data/drinks.json".

        Returns:
            A Path to the real file, or None if not found anywhere.
        """
        # Check mods/ first
        if self.mods_dir.exists():
            for mod_dir in sorted(self.mods_dir.iterdir()):
                if not mod_dir.is_dir():
                    continue
                candidate = mod_dir / logical_path
                if candidate.is_file():
                    return candidate

        # Fall back to base/
        base_candidate = self.base_dir / logical_path
        if base_candidate.is_file():
            return base_candidate

        return None

    # ─────────────────────────────────────────
    # Diagnostics
    # ─────────────────────────────────────────

    def status_report(self) -> str:
        """Return a human-readable overview of the directory structure."""
        lines = ["Game Directory Status", "=" * 52]

        for label, directory in [
            ("Base (protected)", self.base_dir),
            ("Mods", self.mods_dir),
        ]:
            if directory.exists():
                files = [p for p in directory.rglob("*") if p.is_file()]
                writable = os.access(directory, os.W_OK)
                lock_s = "writable" if writable else "READ-ONLY"
                lines.append(
                    f"  {label:<20} {len(files):>4} file(s)  [{lock_s}]"
                )
                lines.append(f"  {'':20} {directory}")
            else:
                lines.append(f"  {label:<20} [MISSING — run ensure_structure()]")

        if self.mods_dir.exists():
            mod_dirs = [d for d in self.mods_dir.iterdir() if d.is_dir()]
            lines.append(f"\n  Installed mods: {len(mod_dirs)}")
            for d in sorted(mod_dirs):
                lines.append(f"    - {d.name}")

        return "\n".join(lines)
