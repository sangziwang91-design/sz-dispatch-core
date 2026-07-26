#!/usr/bin/env python3
"""Dependency-free structural validator for an Agent Skill directory."""

from __future__ import annotations

import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\[[^\]]+\]\((?!https?://|mailto:|#)([^)]+)\)")
REQUIRED_FILES = {
    "SKILL.md",
    "README.md",
    "LICENSE",
    "references/CORE-KERNEL.md",
    "references/EVIDENCE-PROTOCOL.md",
    "references/PERSONAL-OVERLAY.md",
    "references/TEMPLATES.md",
    "references/ADOPTION-GUIDE.md",
    "references/LIMITATIONS.md",
}


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md must start with YAML frontmatter")
    try:
        end = lines[1:].index("---") + 1
    except ValueError as exc:
        raise ValueError("SKILL.md frontmatter is not closed") from exc

    data: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip() or line.startswith(" "):
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip().strip('"\'')
    return data, "\n".join(lines[end + 1 :])


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    skill = root / "SKILL.md"
    if not skill.is_file():
        return ["missing SKILL.md"]

    text = skill.read_text(encoding="utf-8")
    try:
        metadata, _ = parse_frontmatter(text)
    except ValueError as exc:
        return [str(exc)]

    name = metadata.get("name", "")
    description = metadata.get("description", "")
    if not name:
        errors.append("frontmatter missing name")
    elif not NAME_RE.fullmatch(name):
        errors.append("name must contain lowercase letters, numbers, and single hyphens only")
    if root.name != name:
        errors.append(f"directory name '{root.name}' must match skill name '{name}'")
    if not description:
        errors.append("frontmatter missing description")
    elif len(description) > 1024:
        errors.append("description exceeds 1024 characters")
    if len(text.splitlines()) > 500:
        errors.append("SKILL.md exceeds recommended 500 lines")

    for rel in sorted(REQUIRED_FILES):
        if not (root / rel).is_file():
            errors.append(f"missing required file: {rel}")

    for md in root.rglob("*.md"):
        content = md.read_text(encoding="utf-8")
        for target in LINK_RE.findall(content):
            clean = target.split("#", 1)[0]
            if not clean:
                continue
            resolved = (md.parent / clean).resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                errors.append(f"link escapes skill root: {md.relative_to(root)} -> {target}")
                continue
            if not resolved.exists():
                errors.append(f"broken relative link: {md.relative_to(root)} -> {target}")

    return errors


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    errors = validate(root)
    if errors:
        print("Skill validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Skill validation passed: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
