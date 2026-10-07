"""Regression tests for file safety and acceptance decisions, not document wording."""

import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "r-package-engineer" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import check_package
import scaffold
import validate_skill


class ScaffoldTests(unittest.TestCase):
    def arguments(self, path, **overrides):
        values = dict(name="tinytools", title="Tiny Tools", description="Provides small deterministic tools.",
                      given="Test", family="Maintainer", email="maintainer@example.org", license="MIT")
        values.update(overrides)
        args = [str(path)]
        for key, value in values.items():
            args.extend(["--" + key, value])
        return args

    def test_create_and_refuse_second_run_without_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "space in path" / "tinytools"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(scaffold.main(self.arguments(root) + ["--vignette"]), 0)
            before = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            self.assertIn(Path("vignettes/introduction.Rmd"), before)
            self.assertIn(b"MIT + file LICENSE", before[Path("DESCRIPTION")])
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                scaffold.main(self.arguments(root))
            after = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            self.assertEqual(before, after)

    def test_reject_invalid_name_and_metadata_injection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "new"
            for overrides in (dict(name="bad_name"), dict(title="Valid\nImports: injected"),
                              dict(email="bad-email"), dict(name="a")):
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                    scaffold.main(self.arguments(root, **overrides))
                self.assertFalse(root.exists())

    def test_author_input_is_escaped_not_executable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "new"
            with contextlib.redirect_stdout(io.StringIO()):
                scaffold.main(self.arguments(root, given='Test "Quoted" \\Name', license="GPL-3"))
            description = (root / "DESCRIPTION").read_text(encoding="utf-8")
            self.assertIn('Test \\"Quoted\\" \\\\Name', description)
            self.assertFalse((root / "LICENSE").exists())


class CheckTests(unittest.TestCase):
    def test_runner_never_accepts_notes_or_incomplete_checks(self):
        cases = [("Status: 1 NOTE\n", False, 1, False),
                 ("Status: OK\n", True, 0, False),
                 ("Status: OK\n", False, 0, True),
                 ("* checking examples ... OK\n", False, 2, False)]
        for status, development, exit_code, acceptance in cases:
            with self.subTest(status=status, development=development), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                package = root / "package"
                package.mkdir()
                (package / "DESCRIPTION").write_text("Package: tinytools\n", encoding="utf-8")
                output = root / "checks"
                def logged(command, log, cwd, env):
                    if "build" in command:
                        (cwd / "tinytools_1.0.0.tar.gz").write_bytes(b"fixture artifact")
                    else:
                        check = cwd / "tinytools.Rcheck"
                        check.mkdir()
                        (check / "00check.log").write_text(status, encoding="utf-8")
                    return 0
                command = [str(package), "--output", str(output)]
                if development:
                    command.append("--development")
                with patch.object(check_package, "r_executable", return_value="fixture-R"), \
                     patch.object(check_package, "r_environment", return_value={"LANGUAGE": "en"}), \
                     patch.object(check_package, "run_logged", side_effect=logged), \
                     patch.object(check_package.subprocess, "run", return_value=subprocess.CompletedProcess(
                         [], 0, stdout="R version fixture\n", stderr="")), \
                     contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(check_package.main(command), exit_code)
                summary = json.loads(next(output.glob("run-*/summary.json")).read_text(encoding="utf-8"))
                self.assertEqual(summary["final_acceptance"], acceptance)
                self.assertEqual(len(summary["sha256"]), 64)

    def test_final_status_and_counts(self):
        self.assertEqual(check_package.parse_status("* checking ... OK\nStatus: OK\n"),
                         {"ERROR": 0, "WARNING": 0, "NOTE": 0})
        self.assertEqual(check_package.parse_status("Status: 2 ERRORs, 1 WARNING, 3 NOTEs\n"),
                         {"ERROR": 2, "WARNING": 1, "NOTE": 3})
        self.assertIsNone(check_package.parse_status("* checking ... OK\n"))
        self.assertIsNone(check_package.parse_status("Status: unknown\n"))

    def test_output_cannot_contaminate_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "DESCRIPTION").write_text("Package: tinytools\n", encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                check_package.main([str(root), "--output", str(root / "output")])
            self.assertFalse((root / "output").exists())


class SkillTests(unittest.TestCase):
    def test_broken_links_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "link-test"
            root.mkdir()
            (root / "SKILL.md").write_text(
                "---\nname: link-test\ndescription: A link validation fixture.\n---\n[missing](references/missing.md)\n",
                encoding="utf-8",
            )
            self.assertTrue(any("Broken local link" in issue for issue in validate_skill.validate(root)))


if __name__ == "__main__":
    unittest.main()
