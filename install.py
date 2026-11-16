#!/usr/bin/env python3
"""Install the Decision Keeper skill in one existing project."""

from __future__ import annotations

import argparse
from hashlib import sha256
from pathlib import Path
import re
import shutil
import subprocess


BEGIN = b"<!-- decision-keeper:begin -->"
END = b"<!-- decision-keeper:end -->"
LEGACY_NAMES = {"record-me": "Record Me", "teach-me": "Teach Me"}
PREVIOUS_GUIDANCE = b"""<!-- decision-keeper:begin -->
## Decision Keeper

- Before planning or making a project change, read `docs/decision/decision-keeper.md` in full if present. Follow relevant links recursively, including child links inside topic files, and apply the rules to the work and verification. Read the files fresh for each change request.
- When the user confirms a lasting project decision, corrects an existing choice, or asks to organize the decision files, follow `.agents/skills/decision-keeper/SKILL.md` even if the client did not select it automatically.
<!-- decision-keeper:end -->
"""
GUIDANCE = PREVIOUS_GUIDANCE.replace(
    b"When the user confirms a lasting project decision",
    b"When the user's message starts with `/keep` or `/keep and go`, or the user confirms a lasting project decision",
)
CODEX_SKILL = Path(".agents/skills/decision-keeper")
CLAUDE_SKILL = Path(".claude/skills/decision-keeper")
CODEX_AGENT = Path(".codex/agents/decision_keeper_organizer.toml")
LEGACY_CODEX_AGENT = Path(".codex/agents/teach_me_organizer.toml")
INDEX = Path("docs/decision/decision-keeper.md")
LEGACY_INDEXES = (Path("decision-keeper.md"), Path("record-me.md"), Path("teach-me.md"), Path("Teach me.md"))
LEGACY_TOPIC = re.compile(r"(?:decision|learn|record)-([a-z0-9]+(?:-[a-z0-9]+)*)\.md")
DECISION_LINK = re.compile(rb"- \[[^\]\r\n]+\]\(([^()\r\n]+)\) \xe2\x80\x94 \S[^\r\n]*")
SKILL_FILES = (
    Path("SKILL.md"),
    Path("references/organizer.md"),
    Path("scripts/check_tree.py"),
)
LEGACY_GUIDANCE_HASHES = {
    "17a7fecafe16b65280e344ba1da5f9ae8b384739214828d7ee7f241a0a95c2ce",
    "6cef14f67653273acc543817812c654a0a94d98398ff0b404b134641648bad16",
}
PREVIOUS_FILE_HASHES = {
    Path("SKILL.md"): "451609a41c52621f12016f6d9b123cf0a157e198e1ad5c6a8daf8f945ac4f80d",
    Path("references/organizer.md"): "f2b07980e15d43f84051d304e6279aff90fc6ac554c2ab8f66a58cc991ef8fe5",
    Path("scripts/check_tree.py"): "f4eae6b0e9e481e4f33c1055b66e77c3c648cebb45ae232e8c6ed9ecde3d72bd",
}
LEGACY_FILE_HASHES = {
    Path("SKILL.md"): {
        "94fa926d974a75b024d1d057ddbd1a3c3fd975ddf9bcba8fb22b6146a45fb20c",
        "d743fce4edbd129dc6d7b6b8a1a298a1ac11a0a3ee06a18bd9d675974bdbce71",
        "23d53fd0e6ef35f149ac23f8f5960220307f2b465b048d099a5e5a96792e4e56",
        "a2bc029dba1952ed42bcefd876099fa5fd7e4293dd038cf278ecb63d036c29dc",
        "0e73e8ac4ee89b3916a693a9c76db9991dad8acfdeaec4d3f6798ef7ae103989",
    },
    Path("references/organizer.md"): {
        "3c627b962029a902d708918a424be4d2d9e1525c78a3990362273e505c051f41",
        "0c8974c364f63f0f2baeda7e27e33efa5efab3040d30b22ec8541280c348107f",
        "c57e6a76767eddddc32c05dccd934dfa2babe6bb1cb47359f48c0ad4e00d8394",
    },
    Path("scripts/check_tree.py"): {
        "c7d3376f4ace7c6efad441896b27479178e460a71b1b9bafe53e66af717d1bba",
        "a591697dd238e2ab6cade30508add8cef897891393a0729c1a3ee582cca58d91",
        "f2846598b1f428509091a191aac1ae386c89cbad9b4e9a44e8dc109c890d503c",
    },
    LEGACY_CODEX_AGENT: {
        "8eda8d349330b0ecd6111d319b3369e460dabd5eb448ddd39f510f5484e788c8",
        "15600fd9c510b66eddf17bce13311b47b782e8a7827a8c477c5fbe5a645ff40f",
    },
    Path(".codex/agents/record_me_organizer.toml"): {
        "2d298335a2a37edc747dc3231355619836a3fffaba91b5ffd506012f5acdfbdc",
    },
}
MANUAL_COMMAND_UPGRADE_HASHES = {
    Path("SKILL.md"): (
        "30cba07091867ce2485242b07308fbe740803b089e20eef42dd9f3e708e19ca7",
        "d3b784623ce618dce089e2c70790194fd16321e164a97f993c1f0985eb2965b4",
    ),
    Path("references/organizer.md"): (
        "89b79b3b69cac286be976aa103ea477fc8f5c85e9da01460f4a806db981deca7",
        "6f95fddb8b6ded36ff6b0c6add0e039baed6af2a74993e62f0a8b1ec845fa71b",
    ),
}


def guidance_for(skill: Path) -> bytes:
    return GUIDANCE.replace(CODEX_SKILL.as_posix().encode(), skill.as_posix().encode())


def read_managed_block(contents: bytes, skill: Path, name: Path) -> tuple[int, int, bool] | None:
    markers = [(BEGIN, END, None)]
    for slug in LEGACY_NAMES:
        markers.append((f"<!-- {slug}:begin -->".encode(), f"<!-- {slug}:end -->".encode(), slug))
    matches = [(begin, end, slug) for begin, end, slug in markers if begin in contents or end in contents]
    if not matches:
        return None

    if len(matches) != 1:
        raise ValueError(f"Review the markers around the Decision Keeper block in {name}.")
    begin, end_marker, legacy = matches[0]
    start = contents.find(begin)
    end = contents.find(end_marker)
    if contents.count(begin) != 1 or contents.count(end_marker) != 1 or end < start:
        raise ValueError(f"Review the markers around the Decision Keeper block in {name}.")
    end += len(end_marker)
    block = contents[start:end].replace(b"\r\n", b"\n")
    expected = guidance_for(skill).rstrip(b"\n")
    previous = PREVIOUS_GUIDANCE.replace(CODEX_SKILL.as_posix().encode(), skill.as_posix().encode()).rstrip(b"\n")
    legacy_index_guidance = previous.replace(b"`docs/decision/decision-keeper.md`", b"the root `decision-keeper.md`")
    if legacy:
        expected = legacy_index_guidance.replace(b"decision-keeper", legacy.encode()).replace(
            b"Decision Keeper", LEGACY_NAMES[legacy].encode()
        )
    known_legacy = legacy == "teach-me" and skill == CODEX_SKILL and sha256(block).hexdigest() in LEGACY_GUIDANCE_HASHES
    if block != expected and not (not legacy and block in (previous, legacy_index_guidance)) and not known_legacy:
        raise ValueError(f"Review the edited instructions block in {name} before installing Decision Keeper.")
    return start, end, block != guidance_for(skill).rstrip(b"\n")


def reject_symlinks(root: Path, path: Path) -> None:
    for location in (path, *path.parents):
        if location == root:
            break
        if location.is_symlink():
            raise ValueError(f"Resolve the symlink at {location.relative_to(root)} before installing.")


def migrate_decisions(root: Path, index: Path) -> dict[Path, tuple[Path, bytes]]:
    """Plan a move to the new index and nested topic directories."""
    targets = {index: root / INDEX}
    destinations = {root / INDEX}
    pending = [index]
    writes = {}
    while pending:
        path = pending.pop()
        target = targets[path]
        child_dir = target.parent if path == index else target.parent / target.stem.removeprefix("decision-")
        updated = []
        for line in path.read_bytes().splitlines(keepends=True):
            match = DECISION_LINK.fullmatch(line.rstrip(b"\r\n"))
            if match:
                link = Path(match[1].decode("utf-8"))
                old_topic = LEGACY_TOPIC.fullmatch(link.name)
                if link.is_absolute() or not old_topic:
                    raise ValueError(f"Review the topic link in {path.relative_to(root)}: {link}")
                linked = path.parent / link
                reject_symlinks(root, linked)
                linked = linked.resolve(strict=True)
                if not linked.is_relative_to(root / "docs") or not linked.is_file():
                    raise ValueError(f"Review the topic link in {path.relative_to(root)}: {link}")
                if linked in targets:
                    raise ValueError(f"Topic is linked more than once: {linked.relative_to(root)}")
                destination = child_dir / f"decision-{old_topic[1]}.md"
                if destination in destinations:
                    raise ValueError(f"Two topics would move to {destination.relative_to(root)}.")
                targets[linked] = destination
                destinations.add(destination)
                pending.append(linked)
                new_link = destination.relative_to(target.parent).as_posix().encode("utf-8")
                line = line[:match.start(1)] + new_link + line[match.end(1):]
            updated.append(line)
        writes[path] = b"".join(updated)

    for target in targets.values():
        reject_symlinks(root, target)
        if target.exists():
            raise ValueError(f"A different file already exists at {target.relative_to(root)}.")
    return {source: (targets[source], contents) for source, contents in writes.items()}


def install(project: Path, evidence: Path | None = None, client: str = "codex") -> None:
    root = project.expanduser().resolve(strict=True)
    if not root.is_dir() or root in {Path(root.anchor), Path.home().resolve()}:
        raise ValueError("Choose a project directory, not the filesystem root or your home directory.")
    if shutil.which("git"):
        git = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], cwd=root,
            capture_output=True, text=True, check=False,
        )
        if git.returncode == 0 and Path(git.stdout.strip()).resolve() != root:
            raise ValueError(f"Use the repository root: {git.stdout.strip()}")

    agents = root / "AGENTS.md"
    claude_files = (root / "CLAUDE.md", root / ".claude/CLAUDE.md")
    instructions = agents
    skill = CODEX_SKILL
    if client == "claude":
        instructions = next((path for path in claude_files if path.exists() or path.is_symlink()), claude_files[0])
        skill = CLAUDE_SKILL

    files = {CODEX_SKILL / file: skill / file for file in SKILL_FILES}
    legacy_files = {skill.with_name(slug) / file: file for slug in LEGACY_NAMES for file in SKILL_FILES}
    overrides = []
    if client == "codex":
        files[CODEX_AGENT] = CODEX_AGENT
        legacy_files[LEGACY_CODEX_AGENT] = LEGACY_CODEX_AGENT
        legacy_agent = CODEX_AGENT.with_name("record_me_organizer.toml")
        legacy_files[legacy_agent] = legacy_agent
        overrides = [root / "AGENTS.override.md"]
    guidance = guidance_for(skill)
    indexes = (INDEX, *LEGACY_INDEXES)
    for file in (*indexes, *files.values(), *legacy_files):
        reject_symlinks(root, root / file)
    for path in (instructions, *overrides):
        reject_symlinks(root, path)
    if any(path.exists() and path.read_bytes().strip() for path in overrides):
        raise ValueError("Root AGENTS.override.md takes precedence. Reconcile it with AGENTS.md before installing.")

    instructions_name = instructions.relative_to(root).as_posix()
    if not instructions.is_file():
        raise ValueError(f"The project must already have {instructions_name} before installing Decision Keeper.")
    old_instructions = instructions.read_bytes()
    managed = read_managed_block(old_instructions, skill, instructions.relative_to(root))
    present_indexes = [root / file for file in indexes if (root / file).exists()]
    if len(present_indexes) > 1:
        raise ValueError("Multiple decision index files exist. Reconcile their contents before installing Decision Keeper.")
    index = present_indexes[0] if present_indexes else None
    already_installed = managed is not None
    if index and not already_installed:
        other_files = claude_files if client == "codex" else (agents,)
        other_skill = CLAUDE_SKILL if client == "codex" else CODEX_SKILL
        for path in other_files:
            if path.is_file() and path.resolve() == path:
                if read_managed_block(path.read_bytes(), other_skill, path.relative_to(root)):
                    already_installed = True
                    break
    if index and (not already_installed or not index.is_file()):
        raise ValueError(f"Review the existing {index.name} before enabling Decision Keeper.")

    migrations = {}
    if index and index != root / INDEX:
        migrations = migrate_decisions(root, index)

    if evidence is not None:
        knowledge = (root / evidence).resolve(strict=True)
        if not knowledge.is_relative_to(root) or not knowledge.is_file():
            raise ValueError("Choose an existing project knowledge or data file inside the project.")
        if (knowledge in present_indexes or knowledge.is_relative_to(root / INDEX.parent)
                or knowledge.is_relative_to(root / ".agents")
                or knowledge.is_relative_to(root / ".claude/skills") or knowledge.is_relative_to(root / ".git")):
            raise ValueError("Choose a pre-existing project knowledge or data file, independent of Decision Keeper.")
        extra_guidance = old_instructions
        if managed:
            start, end, _ = managed
            extra_guidance = old_instructions[:start] + old_instructions[end:]
        if not knowledge.stat().st_size or (knowledge == instructions and not extra_guidance.strip()):
            raise ValueError("Choose a nonempty project knowledge or data file.")

    package = Path(__file__).resolve().parent
    updates = {}
    for source_file, target_file in files.items():
        source = (package / source_file).read_bytes()
        target = root / target_file
        if target.exists():
            existing = target.read_bytes()
            if existing == source:
                continue
            key = source_file.relative_to(CODEX_SKILL) if source_file.is_relative_to(CODEX_SKILL) else source_file
            known_hashes = (PREVIOUS_FILE_HASHES.get(key), *MANUAL_COMMAND_UPGRADE_HASHES.get(key, ()))
            if sha256(existing).hexdigest() not in known_hashes:
                raise ValueError(f"A different file already exists at {target_file}.")
        updates[target] = source

    obsolete = []
    for file, legacy_key in legacy_files.items():
        path = root / file
        if not path.exists():
            continue
        if sha256(path.read_bytes()).hexdigest() not in LEGACY_FILE_HASHES[legacy_key]:
            raise ValueError(f"Review the customized file at {file} before migrating to Decision Keeper.")
        obsolete.append(path)

    newline = b"\r\n" if b"\r\n" in old_instructions else b"\n"
    new_instructions = old_instructions
    if managed and managed[2]:
        start, end, _ = managed
        new_block = guidance.rstrip(b"\n").replace(b"\n", newline)
        new_instructions = old_instructions[:start] + new_block + old_instructions[end:]
    elif not managed:
        prefix = old_instructions
        if prefix and not prefix.endswith(newline * 2):
            prefix += newline if prefix.endswith(newline) else newline * 2
        new_instructions = prefix + guidance.replace(b"\n", newline)
    if client == "codex" and new_instructions != old_instructions and len(new_instructions) > 32 * 1024:
        raise ValueError("The updated AGENTS.md would exceed the 32 KiB project guidance limit. Shorten it before installing.")

    for target, source in updates.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source)
    for target, contents in migrations.values():
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as file:
            file.write(contents)
    if new_instructions != old_instructions:
        instructions.write_bytes(new_instructions)
    for path in (*migrations, *obsolete):
        path.unlink()
    print(f"Decision Keeper is set up in {root}. Start a new session from the project root.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path, help="root of the project to enable")
    parser.add_argument("evidence", type=Path, nargs="?", help="optional existing project knowledge file, relative to the root")
    parser.add_argument("--client", choices=("codex", "claude"), default="codex", help="coding agent to enable (default: codex)")
    args = parser.parse_args()
    try:
        install(args.project, args.evidence, args.client)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Decision Keeper setup stopped: {error}\n")
