#!/usr/bin/env python3
"""Replace one selected DOI in a group's research line."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"


def normalize_doi(value: str) -> str:
    value = value.strip()
    value = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value, flags=re.IGNORECASE)
    value = re.sub(r"^doi:\s*", "", value, flags=re.IGNORECASE)
    return value.strip()


def looks_like_doi(value: str) -> bool:
    return bool(value) and "/" in value and not re.search(r"\s", value)


def read_group(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"Missing YAML front matter in {path}")
    parts = text.split("---", 2)
    if len(parts) != 3:
        raise ValueError(f"Invalid front matter in {path}")
    data = yaml.safe_load(parts[1]) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Front matter must be a mapping in {path}")
    return data, parts[2]


def write_group(path: Path, data: dict, body: str) -> None:
    front_matter = yaml.safe_dump(
        data,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=1000,
    )
    content = f"---\n{front_matter}---{body}"
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        delete=False,
    ) as temporary:
        temporary.write(content)
        temporary_path = Path(temporary.name)
    temporary_path.replace(path)


def available_groups() -> list[tuple[str, Path, dict, str]]:
    groups = []
    for path in sorted(CONTENT_DIR.glob("*/_index.md")):
        group = path.parent.name
        data, body = read_group(path)
        lines = data.get("research_lines")
        if isinstance(lines, list) and lines:
            groups.append((group, path, data, body))
    return groups


def choose_index(prompt_text: str, items: list[object]) -> int:
    while True:
        raw = input(prompt_text).strip()
        if raw.isdigit() and 1 <= int(raw) <= len(items):
            return int(raw) - 1
        print(f"Enter a number from 1 to {len(items)}.", file=sys.stderr)


def select_group(
    groups: list[tuple[str, Path, dict, str]], requested: str | None
) -> tuple[str, Path, dict, str]:
    if requested:
        for entry in groups:
            if entry[0] == requested:
                return entry
        valid = ", ".join(entry[0] for entry in groups)
        raise ValueError(f"Unknown group '{requested}'. Available groups: {valid}")
    print("\nResearch groups:")
    for index, (group, _, _, _) in enumerate(groups, start=1):
        print(f"  {index}. {group}")
    return groups[choose_index("Group number: ", groups)]


def select_line(lines: list[dict]) -> dict:
    print("\nResearch lines:")
    for index, line in enumerate(lines, start=1):
        slug = line.get("slug", "")
        title = line.get("title") or line.get("eyebrow") or slug
        print(f"  {index}. {title} ({slug})")
    return lines[choose_index("Research line number: ", lines)]


def select_doi(dois: list[str]) -> int:
    if not dois:
        raise ValueError("The selected research line has no DOI entries.")
    print("\nSelected publications:")
    for index, doi in enumerate(dois, start=1):
        print(f"  {index}. {doi or '[empty DOI]'}")
    return choose_index("Publication number to replace: ", dois)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Replace a selected DOI in a group's research line."
    )
    parser.add_argument("--group", help="Group slug, for example matcat or polkt.")
    parser.add_argument(
        "--no-regenerate",
        action="store_true",
        help="Only update the group index; do not regenerate the research-line page.",
    )
    args = parser.parse_args(argv)

    groups = available_groups()
    if not groups:
        print("No groups with research lines were found.", file=sys.stderr)
        return 1

    try:
        group, path, data, body = select_group(groups, args.group)
        lines = data["research_lines"]
        line = select_line(lines)
        dois = line.get("dois")
        if not isinstance(dois, list):
            raise ValueError("The selected research line has no valid 'dois' list.")
        replacement_index = select_doi([str(doi) for doi in dois])
        old_doi = str(dois[replacement_index])
        while True:
            new_doi = normalize_doi(input(f"Replacement DOI (current: {old_doi}): "))
            if not looks_like_doi(new_doi):
                print("The replacement must look like a DOI, for example 10.1000/example.", file=sys.stderr)
                continue
            if new_doi in {str(doi).strip() for index, doi in enumerate(dois) if index != replacement_index}:
                print("That DOI is already selected in this research line.", file=sys.stderr)
                continue
            break

        title = line.get("title") or line.get("eyebrow") or line.get("slug", "")
        print("\n=== Research publication replacement ===")
        print(f"Group:          {group}")
        print(f"Research line:  {title}")
        print(f"Replacing:      {old_doi}")
        print(f"Replacement:    {new_doi}")
        print("=========================================\n")
        if input("Save this replacement? [Y/n]: ").strip().lower() in {"n", "no"}:
            print("Cancelled; no changes written.")
            return 0

        dois[replacement_index] = new_doi
        write_group(path, data, body)
        if not args.no_regenerate:
            slug = str(line.get("slug") or "")
            if not slug:
                raise ValueError("The selected research line has no slug.")
            generator = ROOT / "scripts" / "generate_research_pages.py"
            result = subprocess.run(
                [
                    sys.executable,
                    str(generator),
                    "--group",
                    group,
                    "--slug",
                    slug,
                    "--force",
                ],
                cwd=ROOT,
                check=False,
            )
            if result.returncode != 0:
                print(
                    "The DOI was saved, but regenerating the research page failed.",
                    file=sys.stderr,
                )
                return result.returncode
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Updated {path}")
    if args.no_regenerate:
        print("Research page regeneration skipped (--no-regenerate).")
    else:
        print("Research-line page regenerated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
