#!/usr/bin/env python3
"""Check the decision tree from the Decision Keeper project root."""

from pathlib import Path
import re
import sys


TOPIC_LINK = re.compile(r"- \[[^\]]+\]\(([^()]+)\) — \S.*")
TOPIC_FILE = re.compile(r"decision-[a-z0-9]+(?:-[a-z0-9]+)*\.md")
LIMIT = 10


def check_tree(root: Path) -> tuple[int, list[str]]:
    root = root.resolve()
    directory = root / "docs/decision"
    index = directory / "decision-keeper.md"
    if directory.resolve() != directory:
        return 0, ["docs/decision must be a directory inside the project."]
    if (root / index.name).exists():
        return 0, ["Move the old root decision index to docs/decision/decision-keeper.md."]
    if not index.exists() and any(directory.rglob("decision-*.md")):
        return 0, ["Decision files require an index at docs/decision/decision-keeper.md."]
    if not index.exists() and not index.is_symlink():
        return 0, []
    if index.is_symlink() or not index.is_file():
        return 0, ["docs/decision/decision-keeper.md must be a regular file."]

    pending = [index]
    linked_from = {index: "decision index"}
    decisions = {}
    errors = []
    while pending:
        file = pending.pop()
        relative = file.relative_to(root)
        try:
            lines = file.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as exc:
            errors.append(f"{relative}: could not read decision file ({exc})")
            continue

        child_dir = directory if file == index else file.parent / file.stem.removeprefix("decision-")
        count = 0
        for number, line in enumerate(lines, start=1):
            if not line.startswith("- "):
                continue
            location = f"{relative}:{number}"
            if not line.startswith("- ["):
                count += 1
                rule = line[2:].strip()
                if not rule:
                    errors.append(f"{location}: empty decision")
                elif rule in decisions:
                    errors.append(f"{location}: decision also appears at {decisions[rule]}")
                else:
                    decisions[rule] = location
                continue

            match = TOPIC_LINK.fullmatch(line)
            if not match:
                errors.append(f"{location}: use a relative topic link followed by its description")
                continue
            path = Path(match[1])
            try:
                target = (file.parent / path).resolve(strict=True)
            except (OSError, RuntimeError, ValueError):
                errors.append(f"{location}: broken topic link ({path})")
                continue
            if target in linked_from:
                errors.append(f"{location}: topic is already linked from {linked_from[target]}")
            elif (target.parent != child_dir or path != (child_dir / target.name).relative_to(file.parent)
                    or (file.parent / path) != target
                    or not TOPIC_FILE.fullmatch(target.name) or not target.is_file()):
                errors.append(f"{location}: link to a decision-*.md file in {child_dir.relative_to(root)}")
            else:
                linked_from[target] = location
                pending.append(target)

        if count > LIMIT:
            errors.append(f"{relative}: {count} active decisions (limit {LIMIT})")

    for file in sorted(directory.rglob("decision-*.md")):
        if file not in linked_from:
            errors.append(f"{file.relative_to(root)}: decision file is not linked from the index")

    return len(linked_from), errors


if __name__ == "__main__":
    files, errors = check_tree(Path.cwd())
    if errors:
        print("\n".join(errors), file=sys.stderr)
        sys.exit(1)
    print(f"Checked {files} Decision Keeper decision files.")
