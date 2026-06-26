"""
integrity.py — Point 3: Cryptographic Integrity Verification
=============================================================
Generates a SHA-256 manifest of base game files, optionally signs it
with RSA-PSS, and verifies files on demand (think: Steam's
"Verify Integrity of Game Files", but rolled yourself).

Pipeline:
  1. generate_key_pair()  — one-time setup; keep private key off disk
  2. generate_manifest()  — hash every file in base/
  3. save_manifest()      — write JSON + optional .sig file
  4. verify_manifest()    — check hashes + signature on game launch

Dependencies (signing/verification only):
    pip install cryptography
"""

import base64
import hashlib
import json
import os
import stat
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

try:
    from cryptography.hazmat.primitives import hashes as _ch
    from cryptography.hazmat.primitives import serialization as _cs
    from cryptography.hazmat.primitives.asymmetric import padding as _cp
    from cryptography.hazmat.primitives.asymmetric import rsa as _cr
    from cryptography.exceptions import InvalidSignature

    _CRYPTO = True
except ImportError:
    _CRYPTO = False

# Files to skip when building the manifest (they're generated, not source)
_ALWAYS_SKIP = {"manifest.json", "manifest.sig"}


# ─────────────────────────────────────────────────────────────────────────────
# Exceptions
# ─────────────────────────────────────────────────────────────────────────────

class IntegrityError(Exception):
    """Raised when a structural problem prevents verification from running at all.
    (e.g. manifest file is missing).  Verification *failures* are reported
    inside VerificationResult, not raised as exceptions."""


# ─────────────────────────────────────────────────────────────────────────────
# Result object
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class VerificationResult:
    """Full report of a single verify_manifest() run."""
    passed: bool
    checked: int  # total files in manifest
    failed: list[str] = field(default_factory=list)  # hash mismatch
    missing: list[str] = field(default_factory=list)  # in manifest, not on disk
    extra: list[str] = field(default_factory=list)  # on disk, not in manifest
    signature_valid: bool | None = None  # None = not checked

    def summary(self) -> str:
        status = "PASSED" if self.passed else "FAILED"
        lines = [f"Integrity check: {status}", f"  Checked   : {self.checked} file(s)"]

        if self.failed:
            lines.append(f"  Modified  : {len(self.failed)} file(s) (hash mismatch)")
            for p in self.failed:
                lines.append(f"    x {p}")

        if self.missing:
            lines.append(f"  Missing   : {len(self.missing)} file(s)")
            for p in self.missing:
                lines.append(f"    x {p}")

        if self.extra:
            lines.append(f"  Extra     : {len(self.extra)} untracked file(s)")
            for p in self.extra:
                lines.append(f"    ? {p}")

        if self.signature_valid is not None:
            sig_s = "valid" if self.signature_valid else "INVALID"
            lines.append(f"  Signature : {sig_s}")
        else:
            lines.append("  Signature : not checked (no public key supplied)")

        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _hash_file(path: Path) -> str:
    """SHA-256 of a file.  Reads in 64 KiB chunks so large assets don't OOM."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65_536), b""):
            h.update(chunk)
    return h.hexdigest()


def _need_crypto(action: str) -> None:
    if not _CRYPTO:
        raise RuntimeError(
            f"{action} requires the cryptography package.\n"
            "    pip install cryptography"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 1. Key generation  (run once, during your build/release pipeline)
# ─────────────────────────────────────────────────────────────────────────────

def generate_key_pair(key_dir: Path) -> tuple[Path, Path]:
    """
    Generate an RSA-2048 key pair and save as PEM files under key_dir.

    Workflow:
      - Store the PRIVATE key somewhere secure and off the shipped game.
      - Bundle the PUBLIC key inside your game binary or a read-only asset.
      - The private key signs the manifest at release time.
      - The public key is used by the game at startup to verify the manifest.

    Returns:
        (private_key_path, public_key_path)
    """
    _need_crypto("generate_key_pair")
    key_dir = Path(key_dir)
    key_dir.mkdir(parents=True, exist_ok=True)

    private_key = _cr.generate_private_key(public_exponent=65537, key_size=2048)
    private_path = key_dir / "manifest_private.pem"
    public_path = key_dir / "manifest_public.pem"

    with open(private_path, "wb") as fh:
        fh.write(private_key.private_bytes(
            encoding=_cs.Encoding.PEM,
            format=_cs.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=_cs.NoEncryption(),
        ))
    with open(public_path, "wb") as fh:
        fh.write(private_key.public_key().public_bytes(
            encoding=_cs.Encoding.PEM,
            format=_cs.PublicFormat.SubjectPublicKeyInfo,
        ))

    # Restrict private key to owner read/write only (chmod 600)
    os.chmod(private_path, stat.S_IRUSR | stat.S_IWUSR)

    print(f"Key pair generated:")
    print(f"  private → {private_path}  (keep secret, do NOT ship)")
    print(f"  public  → {public_path}   (safe to ship with game)")
    return private_path, public_path


# ─────────────────────────────────────────────────────────────────────────────
# 2. Manifest generation  (run during your build/release pipeline)
# ─────────────────────────────────────────────────────────────────────────────

def generate_manifest(
        base_dir: Path,
        game_version: str,
        *,
        extra_skip: set[str] | None = None,
) -> dict:
    """
    Walk every file under base_dir, compute its SHA-256 and byte size,
    and return a manifest dict.  Does not write anything to disk yet.

    Args:
        base_dir:     The protected base game content directory.
        game_version: Version string to embed in the manifest (e.g. "1.0.0").
        extra_skip:   Additional relative filenames to exclude.

    Returns:
        A dict ready to be passed to save_manifest().
    """
    base_dir = Path(base_dir)
    skip = _ALWAYS_SKIP | (extra_skip or set())
    records = []

    for file_path in sorted(base_dir.rglob("*")):
        if not file_path.is_file():
            continue
        rel = file_path.relative_to(base_dir).as_posix()
        if rel in skip:
            continue
        records.append({
            "path": rel,
            "sha256": _hash_file(file_path),
            "size": file_path.stat().st_size,
        })
        print(f"  hashed {rel}")

    manifest = {
        "game_version": game_version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "file_count": len(records),
        "files": records,
    }
    print(f"\nManifest built: {len(records)} file(s) for game v{game_version}")
    return manifest


# ─────────────────────────────────────────────────────────────────────────────
# 3. Saving  (with optional RSA-PSS signature)
# ─────────────────────────────────────────────────────────────────────────────

def save_manifest(
        manifest: dict,
        manifest_path: Path,
        *,
        private_key_path: Path | None = None,
) -> None:
    """
    Serialize the manifest dict to JSON and write it to manifest_path.
    If private_key_path is provided, also write a companion .sig file
    containing a base64-encoded RSA-PSS/SHA-256 signature of the JSON bytes.

    The .sig file covers the exact bytes of manifest.json, so any tampering
    with either file (even whitespace changes) invalidates the signature.
    """
    manifest_path = Path(manifest_path)
    payload = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
    manifest_path.write_bytes(payload)
    print(f"Manifest saved  → {manifest_path}")

    if private_key_path is not None:
        _need_crypto("Manifest signing")
        sig_path = manifest_path.with_suffix(".sig")

        with open(private_key_path, "rb") as fh:
            private_key = _cs.load_pem_private_key(fh.read(), password=None)

        signature = private_key.sign(
            payload,
            _cp.PSS(
                mgf=_cp.MGF1(_ch.SHA256()),
                salt_length=_cp.PSS.MAX_LENGTH,
            ),
            _ch.SHA256(),
        )
        sig_path.write_bytes(base64.b64encode(signature))
        print(f"Signature saved → {sig_path}")


# ─────────────────────────────────────────────────────────────────────────────
# 4. Verification  (called by the game on every startup)
# ─────────────────────────────────────────────────────────────────────────────

def verify_manifest(
        base_dir: Path,
        manifest_path: Path,
        *,
        public_key_path: Path | None = None,
) -> VerificationResult:
    """
    Verify every file in base_dir against the manifest's recorded hashes.
    Optionally verify the manifest JSON has not been tampered with by
    checking its RSA-PSS signature.

    This function DOES NOT raise on verification failures — check
    result.passed for the outcome.  It only raises IntegrityError when
    the manifest or signature file is structurally absent.

    Args:
        base_dir:        The protected base content directory to scan.
        manifest_path:   Path to manifest.json (usually base_dir/manifest.json).
        public_key_path: Optional path to the PEM public key for sig check.

    Returns:
        VerificationResult with full details.
    """
    base_dir = Path(base_dir)
    manifest_path = Path(manifest_path)

    if not manifest_path.exists():
        raise IntegrityError(f"Manifest not found: {manifest_path}")

    payload = manifest_path.read_bytes()
    manifest = json.loads(payload)

    # ── Signature check ───────────────────────────────────────────────────────
    sig_valid: bool | None = None
    if public_key_path is not None:
        _need_crypto("Signature verification")
        sig_path = manifest_path.with_suffix(".sig")
        if not sig_path.exists():
            raise IntegrityError(f"Signature file not found: {sig_path}")

        with open(public_key_path, "rb") as fh:
            pub_key = _cs.load_pem_public_key(fh.read())

        try:
            pub_key.verify(
                base64.b64decode(sig_path.read_bytes()),
                payload,
                _cp.PSS(
                    mgf=_cp.MGF1(_ch.SHA256()),
                    salt_length=_cp.PSS.MAX_LENGTH,
                ),
                _ch.SHA256(),
            )
            sig_valid = True
        except InvalidSignature:
            sig_valid = False

    # ── File hash checks ──────────────────────────────────────────────────────
    expected: dict[str, dict] = {r["path"]: r for r in manifest["files"]}
    failed, missing = [], []

    for rel, record in expected.items():
        fpath = base_dir / rel
        if not fpath.exists():
            missing.append(rel)
        elif _hash_file(fpath) != record["sha256"]:
            failed.append(rel)

    # Files present on disk that are not tracked in the manifest.
    # These aren't failures (mods or temp files land here), but worth reporting.
    extra = [
        fpath.relative_to(base_dir).as_posix()
        for fpath in base_dir.rglob("*")
        if fpath.is_file()
           and fpath.relative_to(base_dir).as_posix() not in expected
           and fpath.relative_to(base_dir).as_posix() not in _ALWAYS_SKIP
    ]

    passed = (
            not failed
            and not missing
            and sig_valid is not False  # None (unchecked) is fine; False (invalid) is not
    )

    return VerificationResult(
        passed=passed,
        checked=len(expected),
        failed=failed,
        missing=missing,
        extra=extra,
        signature_valid=sig_valid,
    )
