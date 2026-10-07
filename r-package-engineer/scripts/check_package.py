#!/usr/bin/env python3
"""Build a source tarball and check it; preserve evidence in a new run directory."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from _common import r_environment, r_executable, run_logged


def parse_status(log_text):
    """Only a final check status proves completion; absent status is not success."""
    matches = re.findall(r"^Status:\s*([^\r\n]*)", log_text, flags=re.MULTILINE)
    if not matches:
        return None
    status = matches[-1].strip()
    if status == "OK":
        return {"ERROR": 0, "WARNING": 0, "NOTE": 0}
    counts = {key: 0 for key in ("ERROR", "WARNING", "NOTE")}
    pairs = re.findall(r"(\d+)\s+(ERROR|WARNING|NOTE)s?\b", status)
    if not pairs:
        return None
    for amount, severity in pairs:
        counts[severity] = int(amount)
    return counts


def parse_note_sections(log_text):
    """R may insert elapsed time before a finding, e.g. '... [16s] NOTE'."""
    return re.findall(r"^\* checking (.*?) \.\.\. (?:\[[^\]\r\n]+\]\s+)?NOTE\s*$",
                      log_text, flags=re.MULTILINE)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--output", required=True, type=Path, help="Artifact parent outside package")
    parser.add_argument("--r", help="R executable, discovered from PATH/Rscript by default")
    parser.add_argument("--rscript", default="Rscript", help="Fallback discovery executable")
    parser.add_argument("--locale", help="Explicit LC_ALL for child processes; use an available locale")
    parser.add_argument("--development", action="store_true", help="Skip PDF manual; NEVER final acceptance")
    args = parser.parse_args(argv)
    package = args.package.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if not (package / "DESCRIPTION").is_file():
        parser.error(f"Not a package root: {package}")
    if output == package or package in output.parents:
        parser.error("Artifact output must be outside the package source directory.")
    try:
        binary = r_executable(args.r, args.rscript)
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        parser.error(str(exc))
    output.mkdir(parents=True, exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix="run-", dir=output))
    env = r_environment(args.locale)
    summary = {
        "package_source": str(package), "started_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_directory": str(run), "mode": "development" if args.development else "full-as-cran",
        "final_acceptance": False, "outcome": "incomplete", "commands": [],
        "locale_environment": {key: env.get(key) for key in ("LANG", "LC_ALL", "LANGUAGE")},
        "check_environment": {key: value for key, value in env.items() if key.startswith("_R_CHECK_")},
    }
    try:
        version = subprocess.run([binary, "--version"], capture_output=True, text=True,
                                 encoding="utf-8", errors="replace",
                                 check=True, env=env)
        version_lines = (version.stdout + version.stderr).splitlines()
        if not version_lines:
            raise ValueError("R --version produced no version information.")
        summary["r_version"] = next((line for line in version_lines if line.startswith("R version")
                                     or line.startswith("R Under development")), version_lines[0])
        summary["platform"] = sys.platform
        build = [binary, "CMD", "build"]
        if args.development:
            build.append("--no-manual")
        build.append(str(package))
        summary["commands"].append(build)
        summary["build_exit_code"] = run_logged(build, run / "build.log", run, env)
        if summary["build_exit_code"] != 0:
            summary["outcome"] = "build-failed"
            return 1
        tarballs = list(run.glob("*.tar.gz"))
        if len(tarballs) != 1:
            summary["outcome"] = "missing-or-ambiguous-tarball"
            return 2
        tarball = tarballs[0]
        summary["tarball"] = str(tarball)
        summary["sha256"] = hashlib.sha256(tarball.read_bytes()).hexdigest()
        command = [binary, "CMD", "check", "--as-cran"]
        if args.development:
            command.append("--no-manual")
        command.append(str(tarball))
        summary["commands"].append(command)
        summary["check_exit_code"] = run_logged(command, run / "check.log", run, env)
        logs = list(run.glob("*.Rcheck/00check.log"))
        if len(logs) != 1:
            summary["outcome"] = "missing-or-ambiguous-check-log"
            return 2
        summary["check_log"] = str(logs[0])
        log_text = logs[0].read_text(encoding="utf-8", errors="replace")
        counts = parse_status(log_text)
        summary["counts"] = counts
        summary["note_sections"] = parse_note_sections(log_text)
        if counts is None:
            summary["outcome"] = "incomplete-check"
            return 2
        if summary["check_exit_code"] != 0 or any(counts.values()):
            summary["outcome"] = "findings-require-review"
            return 1
        if not args.development and summary["check_environment"]:
            summary["outcome"] = "custom-check-environment-requires-review"
            return 1
        summary["outcome"] = "development-pass" if args.development else "technical-pass"
        summary["final_acceptance"] = not args.development
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        summary["outcome"] = "execution-failed"
        summary["error"] = str(exc)
        return 2
    finally:
        summary["finished_utc"] = datetime.now(timezone.utc).isoformat()
        (run / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    sys.exit(main())
