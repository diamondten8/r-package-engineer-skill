#!/usr/bin/env python3
"""Validate skill metadata, local links and Python syntax. Requires PyYAML."""

import argparse
import ast
from pathlib import Path
import re
import sys

import yaml


def validate(root):
    root = Path(root).resolve()
    issues = []
    manifest = root / "SKILL.md"
    if not manifest.is_file():
        return ["Missing SKILL.md"]
    text = manifest.read_text(encoding="utf-8")
    match = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n", text, re.DOTALL)
    if not match:
        return ["SKILL.md needs YAML frontmatter"]
    try:
        metadata = yaml.safe_load(match.group(1))
        if not isinstance(metadata, dict):
            return ["Frontmatter must be a mapping"]
        name = metadata.get("name", "")
        description = metadata.get("description", "")
        if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64:
            issues.append("Invalid skill name")
        if name != root.name:
            issues.append("Folder name must match skill name")
        if not isinstance(description, str) or not description.strip() or len(description) > 1024:
            issues.append("Description must be a non-empty string of at most 1024 characters")
        for key in ("name", "description"):
            if isinstance(metadata.get(key), str) and re.search(r"[<>]", metadata[key]):
                issues.append(f"Angle brackets are not allowed in {key}")
    except yaml.YAMLError as exc:
        issues.append(f"Invalid frontmatter YAML: {exc}")
    for path in root.rglob("*.md"):
        content = path.read_text(encoding="utf-8")
        if re.search(r"\b(?:TODO|TBD|FIXME)\b|\[INSERT[^\]]*\]", content):
            issues.append(f"Unfinished placeholder: {path.relative_to(root)}")
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", content):
            if re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", target) or target.startswith("#"):
                continue
            target = target.split("#", 1)[0].strip("<>")
            resolved = (path.parent / target).resolve()
            if root != resolved and root not in resolved.parents:
                issues.append(f"Local link escapes skill: {path.name}: {target}")
            elif not resolved.exists():
                issues.append(f"Broken local link: {path.name}: {target}")
    for path in (root / "scripts").glob("*.py"):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            issues.append(f"Python syntax: {exc}")
    ui_path = root / "agents" / "openai.yaml"
    if ui_path.exists():
        try:
            ui = yaml.safe_load(ui_path.read_text(encoding="utf-8"))
            interface = ui.get("interface", {})
            short = interface.get("short_description", "")
            if not isinstance(short, str) or not 25 <= len(short) <= 64:
                issues.append("UI short_description must have 25-64 characters")
            prompt = interface.get("default_prompt", "")
            if not isinstance(prompt, str) or "$r-package-engineer" not in prompt:
                issues.append("UI default_prompt must mention $r-package-engineer")
        except (yaml.YAMLError, AttributeError) as exc:
            issues.append(f"Invalid UI metadata: {exc}")
    return issues


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill", type=Path)
    args = parser.parse_args(argv)
    issues = validate(args.skill.resolve())
    for issue in issues:
        print(f"ERROR: {issue}")
    print(f"Skill structure validation: {len(issues)} error(s). Behavioral quality requires review.")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
