"""Shared subprocess helpers. No dependency installation or shell interpolation."""

from pathlib import Path
import os
import shutil
import subprocess


def executable(value):
    candidate = shutil.which(value)
    if candidate:
        return str(Path(candidate).resolve())
    path = Path(value)
    if path.is_file():
        return str(path.resolve())
    raise ValueError(f"Executable not found: {value}. Provision it outside the package.")


def r_environment(locale=None):
    env = os.environ.copy()
    env["LANGUAGE"] = "en"
    env["R_ENVIRON_USER"] = os.devnull
    env["R_PROFILE_USER"] = os.devnull
    if locale:
        env["LC_ALL"] = locale
    return env


def r_executable(explicit=None, rscript="Rscript"):
    if explicit:
        return executable(explicit)
    candidate = shutil.which("R")
    if candidate:
        return str(Path(candidate).resolve())
    runner = executable(rscript)
    result = subprocess.run(
        [runner, "--vanilla", "-e", 'cat(R.home("bin"))'],
        check=True, capture_output=True, text=True, encoding="utf-8", errors="replace", env=r_environment(),
    )
    directory = Path(result.stdout.strip())
    for name in ("R.exe", "R"):
        if (directory / name).is_file():
            return str(directory / name)
    raise ValueError("Cannot locate R; supply --r with the R executable path.")


def run_logged(command, log, cwd, env=None):
    with Path(log).open("w", encoding="utf-8") as stream:
        stream.write(f"Argument vector: {command!r}\n")
        stream.flush()
        result = subprocess.run(
            command, cwd=cwd, env=env or r_environment(),
            stdout=stream, stderr=subprocess.STDOUT, check=False,
        )
    return result.returncode
