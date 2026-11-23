"""Run records: every script run gets its own folder with raw data and a manifest of its method.

    results/runs/<YYYYMMDD-HHMMSS>_<kind>/
        manifest.json   what was run: command, config, seeds, method description, environment
        counts.json     raw measurement counts (the data every number in the report is computed from)
        ...             report files written by the script

Run folders are never overwritten or deleted, so negative results stay in the record.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime
from importlib import metadata
from pathlib import Path

RUNS_DIR = Path(__file__).parent / "results" / "runs"
PACKAGES = ("qiskit", "qiskit-aer", "qiskit-ibm-runtime", "mitiq", "numpy", "scipy")


def _git(*args: str) -> str:
    try:
        out = subprocess.run(["git", *args], cwd=Path(__file__).parent, capture_output=True, text=True, timeout=10)
        return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def environment() -> dict:
    versions = {}
    for name in PACKAGES:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = None
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "packages": versions,
        "git_commit": _git("rev-parse", "HEAD") or None,
        "git_research_dirty": bool(_git("status", "--porcelain", "--", ".")),
    }


PREREGISTRATION = Path(__file__).parent / "PREREGISTRATION.md"


def preregistration_hash() -> str | None:
    """SHA-256 of PREREGISTRATION.md at run time, so results can be tied to the targets they were tested against."""
    if not PREREGISTRATION.exists():
        return None
    return hashlib.sha256(PREREGISTRATION.read_bytes()).hexdigest()


def new_run(kind: str, config: dict, method: list[str]) -> Path:
    """Create a run folder and write its manifest. `method` is a plain-language description."""
    run_id = f"{datetime.now():%Y%m%d-%H%M%S}_{kind}"
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    manifest = {
        "run_id": run_id,
        "kind": kind,
        "created": datetime.now().isoformat(timespec="seconds"),
        "command": " ".join([Path(sys.executable).name, *sys.argv]),
        "method": method,
        "config": config,
        "environment": environment(),
        "preregistration_sha256": preregistration_hash(),
    }
    write_json(run_dir / "manifest.json", manifest)
    return run_dir


def update_manifest(run_dir: Path, **fields) -> None:
    path = run_dir / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest.update(fields)
    write_json(path, manifest)


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=1, default=_default), encoding="utf-8")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _default(value):
    if hasattr(value, "item"):  # numpy scalars
        return value.item()
    if isinstance(value, (set, tuple)):
        return list(value)
    raise TypeError(f"Not JSON serializable: {type(value).__name__}")
