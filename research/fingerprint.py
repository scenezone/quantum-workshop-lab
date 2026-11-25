"""Fingerprints of every run and of the pre-registration, for reviewers.

Writes results/FINGERPRINTS.md with:
  * SHA-256 of the key method files now, and the git commit that last changed each one;
  * a check that Parts A and B of PREREGISTRATION.md are unchanged since the runs that recorded them:
    the earlier versions of the file are rebuilt from today's text and hashed, and the hashes must equal
    those recorded in the run manifests;
  * for every run folder: when it ran, the git commit at run time, the pre-registration hash it recorded,
    and the SHA-256 of every file in the folder.

Anyone can re-run this script and compare the hashes. Changing a single byte of any file changes its hash.

    .venv/Scripts/python fingerprint.py
"""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import runlog

HERE = Path(__file__).parent
RUNS = HERE / "results" / "runs"
KEY_FILES = ("PREREGISTRATION.md", "recipe.py", "heldout.py", "mitigation.py", "folding.py", "hardware.py",
             "hardware_usage.py", "noise_scaling.py", "baseline.py", "runlog.py", "recipe_v2.py", "twirl.py",
             "heldout_v2.py", "mitigation_v2.py", "hardware_v2.py", "v2_design_replay.py")

# Hashes recorded at run time (PREREGISTRATION.md Parts B and D quote them too).
RECORDED = {
    "Part A only (11:14)": "042725112296bf1b863795e1771d82448c1026eb8f3f929b08feeb0ee65b1906",
    "Parts A+B (11:22)": "15bb2568d7fe804d9cf7ad11e92bb2294225ff488fae2255fbc84f208da03a15",
    "Parts A+B+C as committed (before Part D)": "ebbdb7d17bb4643b1c98055f23c791395533b528fb84ab3db83b862fdbbc3d1d",
    "Parts A-D (16:11, recorded by the noise-scaling runs)": "caceaa4bc588c549599fd7a779196a9f0eb3dec831a05cc8319a19d907cc1d15",
    "Parts A-E (16:48, hardware plan; sent to reviewer)": "67e4955c6c969b201cbe20ba4aae09e9a73513f3435ee97b5ecaf9568ea54238",
    "A-E + 2 Part C rows (recorded by the smoke job, 24 Nov 10:42)": "1e6445875334a37c4611fde43823840d633a998d43b3e1367d63e5ef1d0a9685",
    "A-E + 3 Part C rows (recorded by hardware round 1, 10:44)": "97b5eb8abf74fb82a77026cf17e7cd5beb454b5d183af3e38cc27767e95ba3ab",
    "A-E + 4 Part C rows (recorded by hardware round 2, 10:58)": "2a0fb6425bff06ae731eb8e41f85ac2032ffd102dffa1809993db51f7ba74b8f",
    "A-E + 5 Part C rows (recorded by the v2 design runs, 24-25 Nov)": "8b1b6812f12014ee89d96621f21850342c97cf46b6dcba9c8b236df04083ba0f",
}
# Versions of the file recorded by runs: label -> (run folders, number of Part C log rows the file had then).
# The script also checks that each hash above equals the one in those runs' manifest.json.
PART_C_VERSIONS = {
    "Parts A-E (16:48, hardware plan; sent to reviewer)": ((), 1),
    "A-E + 2 Part C rows (recorded by the smoke job, 24 Nov 10:42)": (("20261124-104212_hardware-smoke",), 2),
    "A-E + 3 Part C rows (recorded by hardware round 1, 10:44)": (("20261124-104424_hardware-round1",), 3),
    "A-E + 4 Part C rows (recorded by hardware round 2, 10:58)": (("20261124-105849_hardware-round2",), 4),
    "A-E + 5 Part C rows (recorded by the v2 design runs, 24-25 Nov)": (
        ("20261124-161451_mitigation-v2-train", "20261125-101929_mitigation-v2-train-scales1-2-3",
         "20261125-120531_mitigation-v2-train-partial"), 5),
}
RECIPE_FROZEN = "0b08bb7e96d9046e3be34ada9917c09859d2dba9895d1894d647ad26f1a67428"
RECIPE_V2_FROZEN = "c98dd89d6d4cb794cdefd9c63277734ca5d2d24417f60dcfe522c1b7a957bfd8"  # quoted in Part F (25 Nov 2026)
PART_B_PLACEHOLDER = "## Part B: the recipe\n\n*To be written after the training rerun and before the held-out run.*\n\n---\n\n"
PART_C_EMPTY = "## Part C: deviations log\n\n*(none yet)*\n"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(*args: str) -> str:
    out = subprocess.run(["git", *args], cwd=HERE, capture_output=True, timeout=20)
    return out.stdout.decode("utf-8", errors="replace").strip()


def without_part_f(text: str) -> str:
    """The file before Part F was inserted (Part F sits between Part E and Part C)."""
    if "## Part F:" not in text:
        return text
    return text[: text.index("## Part F:")] + text[text.index("## Part C:"):]


def rebuild_earlier_versions(text: str) -> dict[str, str]:
    """Rebuild the file as it was at 11:14 (Part A only) and 11:22 (A+B), from today's text."""
    part_b = text.index("## Part B:")
    later = [text.index(p) for p in ("## Part D:", "## Part E:", "## Part C:") if p in text]
    part_d = min(later)
    return {
        "Part A only (11:14)": text[:part_b] + PART_B_PLACEHOLDER + PART_C_EMPTY,
        "Parts A+B (11:22)": text[:part_d] + PART_C_EMPTY,
    }


def main() -> None:
    head = git("log", "-1", "--format=%H %ci")
    dirty = bool(git("status", "--porcelain", "--", "."))
    lines = [
        "# Fingerprints",
        "",
        f"Generated {datetime.now():%Y-%m-%d %H:%M} by `python fingerprint.py`. Git HEAD: `{head}`"
        + (" (research folder has uncommitted changes)" if dirty else "") + ".",
        "",
        "SHA-256 is a fingerprint: changing a single byte of a file changes its hash completely. To check, re-run "
        "this script or hash a file yourself (`certutil -hashfile <file> SHA256` on Windows, `sha256sum <file>` "
        "elsewhere).",
        "",
        "## Pre-registration integrity",
        "",
        "Earlier versions of `PREREGISTRATION.md` are rebuilt from today's file and hashed. If a rebuilt hash equals "
        "the hash recorded at run time, that part's text has not changed since. Part C (deviations log) only grows "
        "by rows appended at the end, so each hardware run's version is today's file cut after the log rows it had; "
        "each of those hashes is also checked against the run's `manifest.json`. Part F (recipe v2, 25 Nov) was "
        "inserted before Part C, so versions from before it are rebuilt with Part F removed. The last row is "
        "today's file, which has no earlier record to match.",
        "",
        "| Version | Recorded at run time | Rebuilt / checked now | Match |",
        "|---|---|---|---|",
    ]
    full_text = (HERE / "PREREGISTRATION.md").read_bytes().decode("utf-8")
    text = without_part_f(full_text)  # every recorded version below predates Part F
    rebuilt = {k: sha256(v.encode("utf-8")) for k, v in rebuild_earlier_versions(text).items()}
    raw = subprocess.run(["git", "show", "d65539c:research/PREREGISTRATION.md"], cwd=HERE,
                         capture_output=True, timeout=20).stdout
    if raw:
        rebuilt["Parts A+B+C as committed (before Part D)"] = sha256(raw)
    # Part C (the deviations log) only grows by table rows appended at the end, so the version of the file at
    # any earlier time is today's text cut after its n-th log row. A-D = the 1-row version without Part E.
    c_start = text.index("## Part C:")
    c_lines = text[c_start:].rstrip("\n").split("\n")
    rows = [i for i, line in enumerate(c_lines) if line.startswith("| ") and not line.startswith("| Date ")]

    def with_rows(n: int) -> str:
        return text[:c_start] + "\n".join(c_lines[: rows[n - 1] + 1]) + "\n"

    text_1648 = with_rows(1)
    without_e = text_1648[: text_1648.index("## Part E:")] + text_1648[text_1648.index("## Part C:"):]
    rebuilt["Parts A-D (16:11, recorded by the noise-scaling runs)"] = sha256(without_e.encode("utf-8"))
    for label, (run_names, n_rows) in PART_C_VERSIONS.items():
        rebuilt[label] = sha256(with_rows(n_rows).encode("utf-8"))
        for run_name in run_names:
            in_manifest = runlog.read_json(RUNS / run_name / "manifest.json").get("preregistration_sha256")
            if in_manifest != RECORDED[label]:
                raise SystemExit(f"{run_name}/manifest.json records {in_manifest}, not {RECORDED[label]}")
    current = "Current file (A-F + all Part C log entries)"
    rebuilt[current] = sha256(full_text.encode("utf-8"))
    RECORDED.setdefault(current, rebuilt[current])
    rebuilt["recipe.py (frozen 11:22, quoted in Part B)"] = sha256((HERE / "recipe.py").read_bytes())
    rebuilt["recipe_v2.py (frozen 25 Nov, quoted in Part F)"] = sha256((HERE / "recipe_v2.py").read_bytes())
    recorded_all = {**RECORDED, "recipe.py (frozen 11:22, quoted in Part B)": RECIPE_FROZEN,
                    "recipe_v2.py (frozen 25 Nov, quoted in Part F)": RECIPE_V2_FROZEN}
    for label, recorded in recorded_all.items():
        now = rebuilt.get(label, "n/a")
        lines.append(f"| {label} | `{recorded[:16]}…` | `{now[:16]}…` | {'✅ yes' if now == recorded else '❌ NO'} |")

    # Part F7: files frozen for the v2 held-out test, with the hash the pre-registration quotes for each.
    frozen = re.findall(r"^\| `([\w.]+)` \| [^|]* \| `([0-9a-f]{64})` \|$", full_text, flags=re.M)
    if "## Part F:" in full_text:
        if not frozen:
            raise SystemExit("Part F7 frozen-file table not found or not filled in")
        lines += ["", "## Recipe v2 frozen record (PREREGISTRATION.md Part F7)", "",
                  "| File | Hash in Part F7 | Now | Match |", "|---|---|---|---|"]
        for name, quoted in frozen:
            now = sha256((HERE / name).read_bytes())
            lines.append(f"| `{name}` | `{quoted[:16]}…` | `{now[:16]}…` | {'✅ yes' if now == quoted else '❌ NO'} |")

    lines += ["", "## Key files now", "", "| File | SHA-256 | Last commit touching it |", "|---|---|---|"]
    for name in KEY_FILES:
        path = HERE / name
        if path.exists():
            last = git("log", "-1", "--format=%h %ci", "--", name) or "not committed yet"
            lines.append(f"| `{name}` | `{sha256(path.read_bytes())}` | {last} |")

    lines += ["", "## Runs (newest first)", ""]
    for run in sorted((p for p in RUNS.iterdir() if p.is_dir()), reverse=True):
        manifest_path = run / "manifest.json"
        if not manifest_path.exists():
            continue
        m = runlog.read_json(manifest_path)
        env = m.get("environment", {})
        commit = (env.get("git_commit") or "?")[:7] + (" + uncommitted research changes" if env.get("git_research_dirty") else "")
        prereg = (m.get("preregistration_sha256") or "none recorded")[:16]
        status = " (crashed, see FAILED.md)" if (run / "FAILED.md").exists() else ""
        lines += [
            f"### `{run.name}`{status}",
            "",
            f"Created {m.get('created', '?')} · code at commit `{commit}` · pre-registration `{prereg}…`",
            "",
            "| File | Bytes | SHA-256 |",
            "|---|---|---|",
        ]
        for f in sorted(run.iterdir()):
            if f.is_file():
                lines.append(f"| `{f.name}` | {f.stat().st_size} | `{sha256(f.read_bytes())}` |")
        lines.append("")
    out = HERE / "results" / "FINGERPRINTS.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print("\n".join(lines[10:12 + len(recorded_all)]))
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
