"""Build and sign a minimal TUF repository holding the lease rule pack.

Demo setup: all four role keys live in keys/ on one machine. A real
deployment keeps root and targets keys offline (hardware-backed, with a
threshold on root) and only timestamp/snapshot online. Running this again
publishes a new version and extends the metadata expiry.
"""
from __future__ import annotations

import argparse
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from securesystemslib.signer import CryptoSigner, Signer
from tuf.api.metadata import (
    Metadata, MetaFile, Root, Snapshot, TargetFile, Targets, Timestamp,
)

from leasecheck.updates import TARGET_NAME

ROLES = ("root", "targets", "snapshot", "timestamp")
ROOT_DIR = Path(__file__).resolve().parent.parent


def load_or_create_signers(keys_dir: Path) -> dict[str, Signer]:
    """Load one Ed25519 key per role from PEM files, creating any missing."""
    keys_dir.mkdir(parents=True, exist_ok=True)
    signers: dict[str, Signer] = {}
    for role in ROLES:
        path = keys_dir / f"{role}.pem"
        if path.exists():
            key = serialization.load_pem_private_key(path.read_bytes(), None)
        else:
            key = Ed25519PrivateKey.generate()
            path.write_bytes(key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            ))
        signers[role] = CryptoSigner(key)
    return signers


def make_root(signers: dict[str, Signer], valid_days: int = 365) -> Metadata:
    """Create and sign root.json (version 1) trusting each role's key."""
    expires = _now() + timedelta(days=valid_days)
    root = Root(expires=expires)
    root.consistent_snapshot = False
    for role, signer in signers.items():
        root.add_key(signer.public_key, role)
    md = Metadata(root)
    md.sign(signers["root"])
    return md


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _save(signed, signer: Signer, path: Path) -> None:
    md = Metadata(signed)
    md.sign(signer)
    md.to_file(str(path))


def write_repo(
    repo_dir: Path,
    signers: dict[str, Signer],
    root_md: Metadata,
    rules: bytes,
    version: int,
    valid_days: int = 7,
) -> None:
    """Write metadata/ and targets/ for one repo version."""
    meta, tgt = repo_dir / "metadata", repo_dir / "targets"
    for d in (meta, tgt):
        d.mkdir(parents=True, exist_ok=True)
    expires = _now() + timedelta(days=valid_days)

    targets = Targets(version=version, expires=expires)
    targets.targets[TARGET_NAME] = TargetFile.from_data(
        TARGET_NAME, rules, ["sha256"]
    )
    snapshot = Snapshot(version=version, expires=expires)
    snapshot.meta["targets.json"] = MetaFile(version=version)
    timestamp = Timestamp(version=version, expires=expires)
    timestamp.snapshot_meta = MetaFile(version=version)

    (tgt / TARGET_NAME).write_bytes(rules)
    _save(targets, signers["targets"], meta / "targets.json")
    _save(snapshot, signers["snapshot"], meta / "snapshot.json")
    _save(timestamp, signers["timestamp"], meta / "timestamp.json")
    root_md.to_file(str(meta / "1.root.json"))
    root_md.to_file(str(meta / "root.json"))


def next_version(repo_dir: Path) -> int:
    """One more than the published timestamp version, or 1 for a new repo."""
    path = repo_dir / "metadata" / "timestamp.json"
    return Metadata.from_file(str(path)).signed.version + 1 if path.exists() else 1


def main() -> None:
    """Publish the current rules/lease_rules.yaml as a new signed version."""
    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument("--days", type=int, default=7, help="metadata validity")
    args = parser.parse_args()
    keys_dir, repo_dir = ROOT_DIR / "keys", ROOT_DIR / "repo"
    signers = load_or_create_signers(keys_dir)
    root_file = keys_dir / "root.json"
    if root_file.exists():
        root_md = Metadata.from_file(str(root_file))
    else:
        root_md = make_root(signers)
        root_md.to_file(str(root_file))
    rules = (ROOT_DIR / "rules" / "lease_rules.yaml").read_bytes()
    version = next_version(repo_dir)
    write_repo(repo_dir, signers, root_md, rules, version, args.days)
    (ROOT_DIR / "trusted").mkdir(exist_ok=True)
    shutil.copy(root_file, ROOT_DIR / "trusted" / "root.json")
    print(f"Published version {version} to {repo_dir}")
    print("Serve it with: python -m http.server 8000 --directory repo")


if __name__ == "__main__":
    main()
