"""Fetch the rule pack through TUF so tampered, rolled-back or stale packs
are refused. Falls back to the last verified pack, never to unverified data
from the network."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from tuf.api import exceptions
from tuf.api.metadata import Metadata
from tuf.ngclient import Updater

from leasecheck.core import RULES_PATH

TARGET_NAME = "lease_rules.yaml"
ROOT_PATH = Path(__file__).resolve().parent.parent / "trusted" / "root.json"
CACHE_DIR = Path.home() / ".leasecheck"


@dataclass
class RuleStatus:
    """Outcome of an update check."""

    ok: bool
    rules_path: Path
    message: str
    reason: str = ""


def _fallback(cache_dir: Path, reason: str) -> RuleStatus:
    cached = cache_dir / "targets" / TARGET_NAME
    marker = cache_dir / "last_ok.txt"
    if cached.exists() and marker.exists():
        when = marker.read_text().strip()
        msg = f"Using rules last verified {when}. Update refused: {reason}"
        return RuleStatus(False, cached, msg, reason)
    msg = f"Using bundled rules (not verified). Update refused: {reason}"
    return RuleStatus(False, RULES_PATH, msg, reason)


def fetch_rules(
    metadata_url: str,
    targets_url: str,
    cache_dir: Path = CACHE_DIR,
    root_path: Path = ROOT_PATH,
) -> RuleStatus:
    """Refresh TUF metadata and download the rule pack if it changed.

    Args:
        metadata_url: Base URL of the repo's metadata directory.
        targets_url: Base URL of the repo's targets directory.
        cache_dir: Where verified metadata and targets are cached.
        root_path: The trusted root.json shipped with the app.
    Returns:
        A RuleStatus; ok is True only if the pack was verified fresh now.
    """
    if not root_path.exists():
        return _fallback(cache_dir, "no trusted root.json shipped")
    meta_dir, target_dir = cache_dir / "metadata", cache_dir / "targets"
    for d in (meta_dir, target_dir):
        d.mkdir(parents=True, exist_ok=True)
    try:
        updater = Updater(
            metadata_dir=str(meta_dir),
            metadata_base_url=metadata_url,
            target_dir=str(target_dir),
            target_base_url=targets_url,
            bootstrap=root_path.read_bytes(),
        )
        updater.refresh()
        info = updater.get_targetinfo(TARGET_NAME)
        if info is None:
            return _fallback(cache_dir, "TargetNotFound")
        path = updater.find_cached_target(info) or updater.download_target(info)
    except (exceptions.RepositoryError, exceptions.DownloadError, OSError) as exc:
        return _fallback(cache_dir, type(exc).__name__)
    version = Metadata.from_file(str(meta_dir / "targets.json")).signed.version
    expires = Metadata.from_file(str(meta_dir / "timestamp.json")).signed.expires
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    (cache_dir / "last_ok.txt").write_text(now)
    msg = f"Rule pack v{version} verified by TUF (metadata valid until {expires:%Y-%m-%d})"
    return RuleStatus(True, Path(path), msg)
