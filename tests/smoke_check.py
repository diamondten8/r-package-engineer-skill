#!/usr/bin/env python3
"""Real scaffold -> document -> tests -> build/check smoke, plus AST negative cases."""

import argparse
import json
import re
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "r-package-engineer" / "scripts"
sys.path.insert(0, str(SCRIPTS))
from _common import executable, r_environment
import scaffold


FUNCTION = '''#' Add One to Finite Numeric Values
#'
#' @param x A finite numeric vector.
#' @returns A numeric vector with the same length as `x`.
#' @export
#' @examples
#' add_one(c(0, 2))
add_one <- function(x) {
  validate_numeric(x)
  x + 1
}
'''
HELPER = '''#' @noRd
validate_numeric <- function(x) {
  if (!is.numeric(x) || any(!is.finite(x))) {
    stop("`x` must be a finite numeric vector.", call. = FALSE)
  }
  invisible(NULL)
}
'''
TESTS = '''test_that("addition preserves numeric shape and handles empty input", {
  expect_equal(add_one(c(-1, 0, 2)), c(0, 1, 3))
  expect_equal(add_one(numeric()), numeric())
})
test_that("invalid input produces an actionable error", {
  expect_error(add_one("a"), "finite numeric")
  expect_error(add_one(NA_real_), "finite numeric")
  expect_error(add_one(Inf), "finite numeric")
})
test_that("the validation helper is not exported", {
  expect_false("validate_numeric" %in% getNamespaceExports("tinytools"))
})
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rscript", default="Rscript")
    parser.add_argument("--r")
    parser.add_argument("--full", action="store_true", help="Include manual checks; default development smoke")
    parser.add_argument("--vignette", action="store_true", help="Also build and check the scaffold Rmd vignette")
    parser.add_argument("--output", type=Path, default=ROOT / ".artifacts")
    args = parser.parse_args()
    rscript = executable(args.rscript)
    args.output.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="smoke space-", dir=args.output.resolve()))
    package = work / "tinytools"
    scaffold_args = [str(package), "--name", "tinytools", "--title", "Tiny Numeric Tools",
                   "--description", "Provides deterministic numeric transformations for testing package tooling.",
                   "--given", "Test", "--family", "Maintainer", "--email", "maintainer@example.org",
                   "--license", "MIT"]
    if args.vignette:
        scaffold_args.append("--vignette")
    scaffold.main(scaffold_args)
    (package / "R" / "add-one.R").write_text(FUNCTION, encoding="utf-8")
    (package / "R" / "helpers.R").write_text(HELPER, encoding="utf-8")
    (package / "tests" / "testthat" / "test-add-one.R").write_text(TESTS, encoding="utf-8")
    if args.vignette:
        vignette = package / "vignettes" / "introduction.Rmd"
        with vignette.open("a", encoding="utf-8") as stream:
            stream.write("\n## Numeric transformation\n\n```{r transform}\nadd_one(c(-1, 0, 2))\n```\n")
    # Explicit fixture locale avoids inherited Unix C.UTF-8 on older Windows R.
    locale = ("English_United States.utf8" if sys.platform == "win32" else
              "en_US.UTF-8" if sys.platform == "darwin" else "C.UTF-8")
    env = r_environment(locale)
    def rrun(arguments, expected=0):
        result = subprocess.run([rscript, "--vanilla", *arguments], env=env,
                                capture_output=True, text=True, encoding="utf-8", errors="replace")
        print(result.stdout.encode("ascii", "backslashreplace").decode("ascii"))
        if result.returncode != expected:
            raise RuntimeError(f"Expected exit {expected}, got {result.returncode}: {result.stderr}")
        return result.stdout
    rrun(["-e", 'roxygen2::roxygenise(commandArgs(TRUE)[1])', str(package)])
    rrun([str(SCRIPTS / "validate_package.R"), str(package)])
    bad = package / "R" / "bad.R"
    # Comments/strings do not count as calls; qualified direct calls do.
    bad.write_text('# setwd("wrong")\ntext <- "install.packages()"\n', encoding="utf-8")
    rrun([str(SCRIPTS / "validate_package.R"), str(package)])
    for content, evidence in (
        ('bad <- function() base::setwd("/tmp")\n', "Forbidden call: setwd"),
        ('bad <- function() utils::install.packages("x")\n', "Forbidden call: install.packages"),
        ('bad <- function() library(stats)\n', "Forbidden call: library"),
        ('bad <- function() notdeclared::run()\n', "Undeclared namespace"),
        ('bad <- function() stats:::secret()\n', "non-exported external APIs"),
        ('bad <- function( {\n', "R syntax"),
        ("#' @examples\n#' setwd(tempdir())\nNULL\n", "Forbidden call: setwd"),
    ):
        bad.write_text(content, encoding="utf-8")
        result = rrun([str(SCRIPTS / "validate_package.R"), str(package)], expected=1)
        if evidence not in result:
            raise RuntimeError(f"Missing expected diagnostic: {evidence}")
    bad.unlink()
    bad_vignette = package / "vignettes" / "bad.Rmd"
    bad_vignette.parent.mkdir(exist_ok=True)
    bad_vignette.write_text('```{r}\nsetwd(tempdir())\n```\n', encoding="utf-8")
    diagnostic = rrun([str(SCRIPTS / "validate_package.R"), str(package)], expected=1)
    if "Forbidden call: setwd" not in diagnostic:
        raise RuntimeError("Rmd chunk violation was not detected")
    bad_vignette.unlink()
    if not args.vignette:
        bad_vignette.parent.rmdir()
    rrun(["-e", 'testthat::test_local(commandArgs(TRUE)[1])', str(package)])
    command = [sys.executable, str(SCRIPTS / "check_package.py"), str(package), "--output", str(work / "checks")]
    if args.r:
        command.extend(["--r", args.r])
    command.extend(["--rscript", rscript])
    command.extend(["--locale", locale])
    if not args.full:
        command.append("--development")
    result = subprocess.run(command, env=env, check=False)
    summaries = list((work / "checks").glob("run-*/summary.json"))
    if len(summaries) != 1:
        raise RuntimeError("Check did not leave one evidence summary.")
    summary = json.loads(summaries[0].read_text(encoding="utf-8"))
    counts = summary.get("counts")
    if counts is None or counts["ERROR"] or counts["WARNING"] or summary.get("check_exit_code") != 0:
        raise RuntimeError(f"Real smoke check failed; inspect {summaries[0]}")
    if result.returncode != (1 if counts["NOTE"] else 0):
        raise RuntimeError("Check script did not enforce NOTE review exit status.")
    if not args.full and summary["final_acceptance"]:
        raise RuntimeError("Development smoke incorrectly claims final acceptance.")
    note_sections = re.findall(r"^\* checking (.*?) \.\.\. NOTE$",
                              Path(summary["check_log"]).read_text(encoding="utf-8"), re.MULTILINE)
    expected_fixture_notes = {"CRAN incoming feasibility", "for future file timestamps", "top-level files"}
    if len(note_sections) != counts["NOTE"] or set(note_sections) - expected_fixture_notes:
        raise RuntimeError(f"Unexpected fixture NOTE(s): {note_sections}; inspect {summary['check_log']}")
    # A new package may have incoming NOTE(s); the smoke gate proves mechanics only.
    print(f"Smoke passed; {counts['NOTE']} NOTE(s) require review. Evidence: {summaries[0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
