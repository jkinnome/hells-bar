"""
mod_loader.py — Point 5: Mod Metadata Manifests
================================================
Handles everything that happens *before* a single mod asset is touched:
reading mod.json manifests, validating them, checking game version
compatibility, detecting conflicts, and resolving a valid load order
via a topological sort (Kahn's algorithm).

Expected mod.json format (all fields shown; only starred ones are required):

    {
        "mod_id":          "cool_goblin_reskin",      *
        "version":         "1.2.0",                   *
        "author":          "SomeModder",              *

        "display_name":    "Cool Goblin Reskin",
        "description":     "Makes goblins look cooler.",

        "game_version_min": "1.0.0",
        "game_version_max": "2.99.99",

        "dependencies": [
            "base_creatures",
            { "mod_id": "better_enemies", "version": ">=1.0.0" }
        ],

        "conflicts": ["old_goblin_mod", "ancient_goblin_pack"],

        "load_priority": 60,

        "provides": [
            "sprites/enemies/goblin.png",
            "data/enemies/goblin.json"
        ]
    }

load_priority:
    0   = lowest priority (loaded first, easily overridden by others)
    50  = default
    100 = highest priority (loaded last, overrides everything else)

    In the VFS, a file provided by a higher-priority mod shadows the same
    file from lower-priority mods or from base/.
"""

import json
import re
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path

MANIFEST_FILENAME = "mod.json"

# mod_id must be 3-64 chars: lowercase letters, digits, hyphens, underscores
_VALID_MOD_ID = re.compile(r'^[a-z0-9_\-]{3,64}$')

# Version requirement: an operator followed by a semver string
_REQUIREMENT_RE = re.compile(r'^(>=|<=|==|!=|>|<)\s*(\d+\.\d+\.\d+)$')


# ─────────────────────────────────────────────────────────────────────────────
# Exceptions
# ─────────────────────────────────────────────────────────────────────────────

class ModLoadError(Exception):
    """A mod.json is missing, malformed, or violates a validation rule."""


class DependencyError(ModLoadError):
    """A required dependency is absent, wrong version, or circular."""


class ConflictError(ModLoadError):
    """Two active mods declare a hard mutual conflict."""


# ─────────────────────────────────────────────────────────────────────────────
# Version primitives
# ─────────────────────────────────────────────────────────────────────────────

# A version is represented internally as a 3-tuple of ints: (major, minor, patch)
Version = tuple[int, int, int]


def _parse_version(s: str) -> Version:
    """
    Parse a semver string into a comparable 3-tuple.

    "1.2.3"  →  (1, 2, 3)

    Raises ModLoadError if the format is wrong.
    """
    try:
        parts = tuple(int(x) for x in s.strip().split("."))
        if len(parts) != 3:
            raise ValueError
        return parts  # type: ignore[return-value]
    except ValueError:
        raise ModLoadError(
            f"Invalid version {s!r}. Expected 'major.minor.patch' (e.g. '1.2.3')."
        )


def _fmt_version(v: Version) -> str:
    return ".".join(str(x) for x in v)


@dataclass(frozen=True)
class VersionRequirement:
    """
    A single version constraint, e.g. '>=1.2.0', '==2.0.0', '!=1.0.0'.

    supported operators:  >=  <=  ==  !=  >  <
    """
    operator: str
    version: Version

    @classmethod
    def parse(cls, req: str) -> "VersionRequirement":
        m = _REQUIREMENT_RE.match(req.strip())
        if not m:
            raise ModLoadError(
                f"Invalid version requirement {req!r}. "
                f"Expected e.g. '>=1.2.3', '==2.0.0', '!=1.0.0'."
            )
        return cls(operator=m.group(1), version=_parse_version(m.group(2)))

    def satisfied_by(self, v: Version) -> bool:
        return {
            ">=": v >= self.version,
            "<=": v <= self.version,
            "==": v == self.version,
            "!=": v != self.version,
            ">": v > self.version,
            "<": v < self.version,
        }[self.operator]

    def __str__(self) -> str:
        return f"{self.operator}{_fmt_version(self.version)}"


# ─────────────────────────────────────────────────────────────────────────────
# Manifest data structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class DependencySpec:
    """A single entry in a mod's 'dependencies' list."""
    mod_id: str
    requirement: VersionRequirement | None = None  # None = any version accepted

    @classmethod
    def from_raw(cls, raw: str | dict) -> "DependencySpec":
        """
        Accept either shorthand ("some_mod_id") or full form:
            { "mod_id": "some_mod_id", "version": ">=1.0.0" }
        """
        if isinstance(raw, str):
            return cls(mod_id=raw)
        if isinstance(raw, dict):
            mod_id = raw.get("mod_id", "")
            if not mod_id:
                raise ModLoadError("Dependency entry is missing 'mod_id'.")
            req = VersionRequirement.parse(raw["version"]) if "version" in raw else None
            return cls(mod_id=mod_id, requirement=req)
        raise ModLoadError(
            f"Dependency entries must be a string or dict, got {type(raw).__name__}."
        )


@dataclass
class ModManifest:
    """
    The fully parsed and validated contents of a single mod's mod.json.
    This is the canonical runtime representation of a mod's identity.
    """

    # Required fields
    mod_id: str
    version: Version
    version_str: str  # original string, kept for display
    author: str
    mod_dir: Path  # absolute path to the mod's root directory

    # Optional metadata
    display_name: str = ""
    description: str = ""

    # Compatibility bounds  (None = unbounded)
    game_version_min: Version | None = None
    game_version_max: Version | None = None

    # Relationships
    dependencies: list[DependencySpec] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)  # list of mod_ids

    # VFS integration
    load_priority: int = 50  # 0 lowest → 100 highest override power
    provides: list[str] = field(default_factory=list)  # logical paths overridden

    def __hash__(self) -> int:
        return hash(self.mod_id)

    def __eq__(self, other) -> bool:
        return isinstance(other, ModManifest) and self.mod_id == other.mod_id

    def __repr__(self) -> str:
        return f"<Mod {self.mod_id!r} v{self.version_str}>"

    def compatible_with_game(self, game_ver: Version) -> bool:
        """Return True if game_ver falls within this mod's declared range."""
        if self.game_version_min and game_ver < self.game_version_min:
            return False
        if self.game_version_max and game_ver > self.game_version_max:
            return False
        return True


# ─────────────────────────────────────────────────────────────────────────────
# Manifest loading  (single mod)
# ─────────────────────────────────────────────────────────────────────────────

def load_mod_manifest(mod_dir: Path) -> ModManifest:
    """
    Parse and validate <mod_dir>/mod.json into a ModManifest.

    Validates:
      - JSON is well-formed
      - All required fields are present
      - mod_id matches the naming convention
      - version strings are valid semver
      - load_priority is in [0, 100]
      - dependency entries are well-formed
      - conflicts list is a list of strings

    Raises:
        ModLoadError with a human-readable message on any failure.
    """
    mod_dir = Path(mod_dir)
    manifest_path = mod_dir / MANIFEST_FILENAME

    if not manifest_path.exists():
        raise ModLoadError(f"No {MANIFEST_FILENAME} found in {mod_dir}")

    try:
        data: dict = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ModLoadError(f"Malformed JSON in {manifest_path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ModLoadError(f"{manifest_path}: top-level value must be a JSON object.")

    # ── Required fields ───────────────────────────────────────────────────────
    for required_field in ("mod_id", "version", "author"):
        if required_field not in data:
            raise ModLoadError(
                f"{manifest_path}: missing required field '{required_field}'."
            )

    mod_id = str(data["mod_id"])
    if not _VALID_MOD_ID.match(mod_id):
        raise ModLoadError(
            f"Invalid mod_id {mod_id!r} in {manifest_path}.\n"
            f"  Must be 3–64 characters: lowercase letters, digits, hyphens, underscores."
        )

    version_str = str(data["version"])
    version = _parse_version(version_str)

    # ── Optional game version bounds ──────────────────────────────────────────
    game_version_min: Version | None = None
    game_version_max: Version | None = None

    if "game_version_min" in data:
        game_version_min = _parse_version(str(data["game_version_min"]))
    if "game_version_max" in data:
        game_version_max = _parse_version(str(data["game_version_max"]))

    if (game_version_min and game_version_max
            and game_version_min > game_version_max):
        raise ModLoadError(
            f"{manifest_path}: game_version_min ({data['game_version_min']}) "
            f"is greater than game_version_max ({data['game_version_max']})."
        )

    # ── Dependencies ──────────────────────────────────────────────────────────
    raw_deps = data.get("dependencies", [])
    if not isinstance(raw_deps, list):
        raise ModLoadError(f"{manifest_path}: 'dependencies' must be a list.")
    dependencies = [DependencySpec.from_raw(d) for d in raw_deps]

    # ── Conflicts ─────────────────────────────────────────────────────────────
    raw_conflicts = data.get("conflicts", [])
    if not isinstance(raw_conflicts, list) or not all(
            isinstance(c, str) for c in raw_conflicts
    ):
        raise ModLoadError(
            f"{manifest_path}: 'conflicts' must be a list of mod_id strings."
        )
    conflicts: list[str] = raw_conflicts

    # A mod can't conflict with itself
    if mod_id in conflicts:
        raise ModLoadError(
            f"{manifest_path}: mod_id {mod_id!r} cannot list itself as a conflict."
        )

    # ── Load priority ─────────────────────────────────────────────────────────
    raw_priority = data.get("load_priority", 50)
    try:
        load_priority = int(raw_priority)
    except (TypeError, ValueError):
        raise ModLoadError(
            f"{manifest_path}: 'load_priority' must be an integer, "
            f"got {raw_priority!r}."
        )
    if not (0 <= load_priority <= 100):
        raise ModLoadError(
            f"{manifest_path}: 'load_priority' must be 0–100, got {load_priority}."
        )

    # ── Provides ──────────────────────────────────────────────────────────────
    raw_provides = data.get("provides", [])
    if not isinstance(raw_provides, list) or not all(
            isinstance(p, str) for p in raw_provides
    ):
        raise ModLoadError(
            f"{manifest_path}: 'provides' must be a list of path strings."
        )

    return ModManifest(
        mod_id=mod_id,
        version=version,
        version_str=version_str,
        author=str(data["author"]),
        mod_dir=mod_dir.resolve(),
        display_name=str(data.get("display_name", mod_id)),
        description=str(data.get("description", "")),
        game_version_min=game_version_min,
        game_version_max=game_version_max,
        dependencies=dependencies,
        conflicts=conflicts,
        load_priority=load_priority,
        provides=list(raw_provides),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Manifest loading  (all mods in a directory)
# ─────────────────────────────────────────────────────────────────────────────

def load_all_mods(mods_dir: Path) -> tuple[list[ModManifest], list[str]]:
    """
    Scan every subdirectory of mods_dir for a mod.json and load it.

    Bad mods are NOT raised — they are collected as error strings so the
    rest of the mods can still load.  The game can decide whether to abort
    or just warn the user based on the error list.

    Args:
        mods_dir: The directory to scan (e.g. game_root/mods/).

    Returns:
        (successfully_loaded_mods, error_messages)
    """
    mods_dir = Path(mods_dir)
    mods: list[ModManifest] = []
    errors: list[str] = []

    if not mods_dir.exists():
        return mods, errors

    for entry in sorted(mods_dir.iterdir()):
        if not entry.is_dir():
            continue  # skip loose files in mods/
        try:
            mods.append(load_mod_manifest(entry))
        except ModLoadError as exc:
            errors.append(f"[{entry.name}] {exc}")

    return mods, errors


# ─────────────────────────────────────────────────────────────────────────────
# Validation passes
# ─────────────────────────────────────────────────────────────────────────────

def check_game_compatibility(
        mods: list[ModManifest],
        game_version: str,
) -> list[str]:
    """
    Check every mod's game_version_min / game_version_max against the
    running game version.

    Returns a list of human-readable warning strings.  An empty list means
    all mods are compatible.  These are warnings, not errors — the game
    can choose to load incompatible mods anyway (with a user warning).
    """
    gv = _parse_version(game_version)
    warnings = []

    for mod in mods:
        if not mod.compatible_with_game(gv):
            min_s = _fmt_version(mod.game_version_min) if mod.game_version_min else "any"
            max_s = _fmt_version(mod.game_version_max) if mod.game_version_max else "any"
            warnings.append(
                f"  {mod.mod_id} v{mod.version_str} requires game [{min_s}…{max_s}], "
                f"but running game is v{game_version}."
            )

    return warnings


def detect_conflicts(mods: list[ModManifest]) -> list[str]:
    """
    Find two categories of conflicts among the active mod list:

    1. Explicit conflicts — a mod's 'conflicts' list names another active mod.
       These are hard errors: both mods cannot be active simultaneously by
       the mod author's own declaration.

    2. Implicit file conflicts — two mods both declare the same logical path
       in their 'provides' list.  These are warnings: the higher-priority mod
       wins in the VFS, but the user should know the override is happening.

    Returns a list of human-readable message strings.
    Messages prefixed "[ERROR]" are hard conflicts; "[WARN]" are soft.
    An empty list means no conflicts detected.
    """
    id_map = {m.mod_id: m for m in mods}
    messages = []

    # ── Explicit conflicts ────────────────────────────────────────────────────
    # Deduplicate: if mod_a lists mod_b as conflict, and mod_b also lists mod_a,
    # report it only once.
    seen_pairs: set[frozenset[str]] = set()

    for mod in mods:
        for conflict_id in mod.conflicts:
            if conflict_id not in id_map:
                continue  # conflicted mod isn't installed, no problem
            pair = frozenset({mod.mod_id, conflict_id})
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            other = id_map[conflict_id]
            messages.append(
                f"[ERROR] '{mod.mod_id}' v{mod.version_str} and "
                f"'{other.mod_id}' v{other.version_str} "
                f"declare a hard conflict and are both active."
            )

    # ── Implicit file conflicts ───────────────────────────────────────────────
    providers: dict[str, list[str]] = defaultdict(list)
    for mod in mods:
        for logical_path in mod.provides:
            providers[logical_path].append(mod.mod_id)

    for logical_path, provider_ids in providers.items():
        if len(provider_ids) > 1:
            messages.append(
                f"[WARN]  File conflict on '{logical_path}': "
                f"provided by {provider_ids}. "
                f"Highest load_priority wins."
            )

    return messages


# ─────────────────────────────────────────────────────────────────────────────
# Dependency resolution and load order
# ─────────────────────────────────────────────────────────────────────────────

def resolve_load_order(mods: list[ModManifest]) -> list[ModManifest]:
    """
    Compute a valid load sequence for the given mods using Kahn's topological
    sort algorithm, respecting both dependency ordering and load_priority.

    Rules:
      - If mod A declares a dependency on mod B, B must be loaded before A.
      - Within each "wave" of the sort (mods with no remaining unmet deps),
        mods are ordered by load_priority ascending — so lower-priority mods
        load first and can be overridden by higher-priority ones that load later.
      - A higher load_priority means the mod's assets override lower ones in
        the VFS, because it was the last to register its paths.

    Raises:
        DependencyError: if a required dependency is missing, the installed
                         version doesn't satisfy the constraint, or circular
                         dependencies are detected.
    """
    if not mods:
        return []

    id_map: dict[str, ModManifest] = {m.mod_id: m for m in mods}

    # ── Step 1: validate all declared dependencies exist and satisfy versions ─
    for mod in mods:
        for dep in mod.dependencies:
            if dep.mod_id not in id_map:
                raise DependencyError(
                    f"'{mod.mod_id}' requires '{dep.mod_id}', which is not installed.\n"
                    f"  Install '{dep.mod_id}' or disable '{mod.mod_id}'."
                )
            installed = id_map[dep.mod_id]
            if dep.requirement and not dep.requirement.satisfied_by(installed.version):
                raise DependencyError(
                    f"'{mod.mod_id}' requires '{dep.mod_id} {dep.requirement}', "
                    f"but installed version is v{installed.version_str}."
                )

    # ── Step 2: build the dependency graph ───────────────────────────────────
    # must_come_before[X] = set of mod_ids that X depends on (must load before X)
    must_come_before: dict[str, set[str]] = {m.mod_id: set() for m in mods}
    in_degree: dict[str, int] = {m.mod_id: 0 for m in mods}

    for mod in mods:
        for dep in mod.dependencies:
            if dep.mod_id not in must_come_before[mod.mod_id]:
                must_come_before[mod.mod_id].add(dep.mod_id)
                in_degree[mod.mod_id] += 1

    # ── Step 3: Kahn's algorithm with priority ordering ───────────────────────
    # Seed the queue with mods that have no dependencies, sorted by priority
    # (ascending = lower priority first = loaded first = overridden by later mods)
    ready: deque[ModManifest] = deque(
        sorted(
            (m for m in mods if in_degree[m.mod_id] == 0),
            key=lambda m: m.load_priority,
        )
    )
    result: list[ModManifest] = []

    while ready:
        mod = ready.popleft()
        result.append(mod)

        # Unlock every mod that had this one as a dependency
        for other in mods:
            if mod.mod_id not in must_come_before[other.mod_id]:
                continue
            in_degree[other.mod_id] -= 1
            if in_degree[other.mod_id] == 0:
                # Insert into the queue in priority order (ascending)
                insert_at = len(ready)
                for i, queued in enumerate(ready):
                    if queued.load_priority > other.load_priority:
                        insert_at = i
                        break
                ready.insert(insert_at, other)

    # ── Step 4: circular dependency check ────────────────────────────────────
    if len(result) != len(mods):
        unresolved = sorted(
            {m.mod_id for m in mods} - {m.mod_id for m in result}
        )
        raise DependencyError(
            f"Circular dependency detected.  These mods could not be ordered:\n"
            + "\n".join(f"  - {mid}" for mid in unresolved)
        )

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Priority-aware VFS resolution
# ─────────────────────────────────────────────────────────────────────────────

class ModLoader:
    """
    Thin runtime wrapper that holds the final ordered mod list and provides
    priority-aware file resolution for the game's Virtual File System.

    Instantiate this after resolve_load_order() succeeds.
    """

    def __init__(self, ordered_mods: list[ModManifest], base_dir: Path) -> None:
        self.base_dir = Path(base_dir)
        # Reverse so index 0 = highest priority (searched first)
        self._search_order = list(reversed(ordered_mods))

    def resolve(self, logical_path: str) -> Path | None:
        """
        Find the highest-priority real file for a logical asset path.

        Searches mods highest-priority-first, then falls back to base/.

        Args:
            logical_path: e.g. "sprites/enemies/goblin.png"

        Returns:
            The Path to the winning file, or None if not found anywhere.
        """
        for mod in self._search_order:
            candidate = mod.mod_dir / logical_path
            if candidate.is_file():
                return candidate

        base_candidate = self.base_dir / logical_path
        if base_candidate.is_file():
            return base_candidate

        return None

    def resolve_with_source(self, logical_path: str) -> tuple[Path, str] | None:
        """
        Like resolve(), but also returns a label describing the source
        (useful for debug overlays).

        Returns:
            (real_path, source_label) or None.
            source_label is either "base" or the mod_id that provided the file.
        """
        for mod in self._search_order:
            candidate = mod.mod_dir / logical_path
            if candidate.is_file():
                return candidate, mod.mod_id

        base_candidate = self.base_dir / logical_path
        if base_candidate.is_file():
            return base_candidate, "base"

        return None


# ─────────────────────────────────────────────────────────────────────────────
# Reporting
# ─────────────────────────────────────────────────────────────────────────────

def load_order_report(mods: list[ModManifest]) -> str:
    """
    Format the ordered mod list as a human-readable table.

    The order in this table is the actual load order: index 1 loads first
    (lowest priority), the last entry loads last (highest priority, wins
    all file conflicts).
    """
    if not mods:
        return "No mods loaded."

    col_id = max(len(m.mod_id) for m in mods)
    col_ver = max(len(m.version_str) for m in mods)
    col_id = max(col_id, 6)  # minimum column widths
    col_ver = max(col_ver, 7)

    header = (
        f"{'#':>3}  "
        f"{'Mod ID':<{col_id}}  "
        f"{'Version':>{col_ver}}  "
        f"{'Priority':>8}  "
        f"Author"
    )
    sep = "─" * (3 + 2 + col_id + 2 + col_ver + 2 + 8 + 2 + 20)
    rows = [
        f"{i:>3}  "
        f"{m.mod_id:<{col_id}}  "
        f"{m.version_str:>{col_ver}}  "
        f"{m.load_priority:>8}  "
        f"{m.author}"
        for i, m in enumerate(mods, 1)
    ]
    return "\n".join([header, sep, *rows])
