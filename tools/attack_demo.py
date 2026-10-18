"""Attack demo: serve TUF repos from localhost and try to fool the client.

Run from the project root: python -m tools.attack_demo
Prints a markdown table you can paste into the post.
"""
from __future__ import annotations

import functools
import shutil
import sys
import tempfile
import threading
from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from securesystemslib.signer import CryptoSigner

from leasecheck.updates import RuleStatus, fetch_rules
from tools.tufrepo import ROOT_DIR, load_or_create_signers, make_root, write_repo


class _Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args) -> None:  # silence request logging
        pass


@contextmanager
def serve(directory: Path):
    """Serve a directory over HTTP on a free localhost port."""
    handler = functools.partial(_Quiet, directory=str(directory))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()


def attempt(repo: Path, cache: Path, root: Path) -> RuleStatus:
    """Run the app's update check against a repo served from `repo`."""
    with serve(repo) as base:
        return fetch_rules(f"{base}/metadata/", f"{base}/targets/", cache, root)


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="tuf-demo-"))
    signers = load_or_create_signers(tmp / "keys")
    root_md = make_root(signers)
    root = tmp / "root.json"
    root_md.to_file(str(root))
    rules_v1 = (ROOT_DIR / "rules" / "lease_rules.yaml").read_bytes()
    rules_v2 = rules_v1.replace(b"version: 1", b"version: 2", 1)

    for name, rules, ver in (("v1", rules_v1, 1), ("v2", rules_v2, 2)):
        write_repo(tmp / name, signers, root_md, rules, ver)
    shutil.copytree(tmp / "v2", tmp / "tampered")
    (tmp / "tampered" / "targets" / "lease_rules.yaml").write_bytes(
        rules_v2.replace(b"severity: high", b"severity: low")
    )
    write_repo(tmp / "frozen", signers, root_md, rules_v2, 3, valid_days=-1)
    forged = {**signers, "timestamp": CryptoSigner.generate_ed25519()}
    write_repo(tmp / "forged", forged, root_md, rules_v2, 3)

    rows = []  # (scenario, expected failure or None, status)
    rows.append(("Honest repo", None, attempt(tmp / "v2", tmp / "c1", root)))
    rows.append((
        "Rule pack altered on the mirror (hash mismatch)",
        "LengthOrHashMismatchError",
        attempt(tmp / "tampered", tmp / "c2", root),
    ))
    attempt(tmp / "v2", tmp / "c3", root)  # client now trusts version 2
    rows.append((
        "Rollback to older signed rules (v1 after v2)",
        "BadVersionNumberError",
        attempt(tmp / "v1", tmp / "c3", root),
    ))
    rows.append((
        "Frozen: stale metadata past its expiry",
        "ExpiredMetadataError",
        attempt(tmp / "frozen", tmp / "c4", root),
    ))
    rows.append((
        "Forged timestamp signed with an attacker's key",
        "UnsignedMetadataError",
        attempt(tmp / "forged", tmp / "c5", root),
    ))

    print("| Scenario | Client verdict | Reason |\n|---|---|---|")
    failed = 0
    for scenario, expected, status in rows:
        verdict = "accepted" if status.ok else "refused"
        good = status.ok if expected is None else status.reason == expected
        failed += not good
        print(f"| {scenario} | {verdict} | {status.reason or 'verified'} |"
              f"{'' if good else '  <-- UNEXPECTED'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
