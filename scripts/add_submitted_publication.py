#!/usr/bin/env python3
"""Add a submitted publication to the profiles of its listed authors."""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
import unicodedata
from datetime import date
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SUBMITTED_FILE = ROOT / "data" / "publications" / "submitted.yaml"
PEOPLE_DIR = ROOT / "content" / "people"
GROUP_TAGS = {
    "isom-kt": "ISoM-KT",
    "matcat-kt": "MatCat-KT",
    "bio-kt": "Bio-KT",
    "pol-kt": "POL-KT",
    "noft-kt": "NOFT-KT",
    "moleles-kt": "MolEleS-KT",
    "qcd-kt": "QCD-KT",
    "momag-kt": "MoMag-KT",
}


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalize_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", normalize_text(value))
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]", "", normalized.casefold())


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "publication"


def parse_date(raw: str) -> date:
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Date must use YYYY-MM-DD format.") from exc


def prompt_value(label: str, initial: str = "") -> str:
    suffix = f" [{initial}]" if initial else ""
    return input(f"{label}{suffix}: ").strip() or initial


def prompt_authors() -> list[str]:
    while True:
        raw = input("Authors (separate names with semicolons): ").strip()
        authors = [normalize_text(author) for author in raw.split(";")]
        authors = [author for author in authors if author]
        if authors:
            return authors
        print("Enter at least one author.", file=sys.stderr)


def parse_group_tags(raw: str) -> list[str]:
    tags = []
    invalid = []
    for value in raw.split(","):
        tag = normalize_text(value)
        if not tag:
            continue
        canonical = GROUP_TAGS.get(tag.casefold())
        if canonical is None:
            invalid.append(tag)
        elif canonical not in tags:
            tags.append(canonical)
    if invalid:
        valid = ", ".join(GROUP_TAGS.values())
        raise ValueError(f"Unknown group tag(s): {', '.join(invalid)}. Valid tags: {valid}")
    return tags


def prompt_group_tags() -> list[str]:
    valid_tags = ", ".join(GROUP_TAGS.values())
    while True:
        raw = input(f"Research group tag(s), comma-separated (optional; {valid_tags}): ").strip()
        try:
            return parse_group_tags(raw)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)


def load_members() -> list[dict[str, object]]:
    members = []
    for path in sorted(PEOPLE_DIR.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        if not content.startswith("---"):
            continue
        parts = content.split("---", 2)
        if len(parts) < 3:
            continue
        metadata = yaml.safe_load(parts[1]) or {}
        if not isinstance(metadata, dict):
            continue
        member_id = str(metadata.get("id") or path.stem).strip()
        title = normalize_text(str(metadata.get("title") or path.stem))
        title = re.sub(r"^(Prof\.|Dr\.)\s+", "", title, flags=re.IGNORECASE)
        aliases = metadata.get("publication_names") or [title]
        if not isinstance(aliases, list):
            raise ValueError(f"Invalid publication_names in {path}")
        normalized_aliases = {
            normalize_name(str(alias))
            for alias in [*aliases, title]
            if normalize_name(str(alias))
        }
        members.append({
            "id": member_id,
            "name": title,
            "aliases": normalized_aliases,
        })
    return members


def author_name_variants(author: str) -> set[str]:
    variants = {normalize_name(author)}
    if "," in author:
        family, given = author.split(",", 1)
        variants.add(normalize_name(f"{given} {family}"))
    return {variant for variant in variants if variant}


def matching_members(author: str, members: list[dict[str, object]]) -> list[dict[str, object]]:
    variants = author_name_variants(author)
    return [
        member
        for member in members
        if variants.intersection(member["aliases"])
    ]


def choose_member(author: str, members: list[dict[str, object]]) -> str | None:
    print(f"\nSelect a profile to associate with author: {author}")
    for index, member in enumerate(members, start=1):
        print(f"  {index}. {member['name']}")
    print("  0. Do not associate this author with a profile")
    while True:
        raw = input("Profile number: ").strip()
        if raw.isdigit() and 0 <= int(raw) <= len(members):
            selected = int(raw)
            return str(members[selected - 1]["id"]) if selected else None
        print(f"Enter a number from 0 to {len(members)}.", file=sys.stderr)


def resolve_profile_ids(
    authors: list[str], members: list[dict[str, object]]
) -> list[str]:
    profile_ids = []
    for author in authors:
        matches = matching_members(author, members)
        selected_id: str | None = None
        if len(matches) == 1:
            member = matches[0]
            selected_id = str(member["id"])
            print(f"Matched author '{author}' to profile: {member['name']}")
        elif len(matches) > 1:
            print(f"Author '{author}' matches multiple profiles.")
            selected_id = choose_member(author, matches)
        else:
            print(f"No team profile matched author '{author}'.")
            associate = input("Associate this author with a team member? [y/N]: ").strip().lower()
            if associate in {"y", "yes"}:
                selected_id = choose_member(author, members)
        if selected_id and selected_id not in profile_ids:
            profile_ids.append(selected_id)
    return profile_ids


def load_submissions() -> dict:
    if not SUBMITTED_FILE.exists():
        return {"items": []}
    with SUBMITTED_FILE.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {"items": []}
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        raise ValueError(f"Invalid submitted-publications file: {SUBMITTED_FILE}")
    return data


def submission_exists(data: dict, title: str, authors: list[str]) -> bool:
    normalized_title = normalize_text(title).casefold()
    normalized_authors = {normalize_text(author).casefold() for author in authors}
    for item in data["items"]:
        if normalize_text(str(item.get("title", ""))).casefold() != normalized_title:
            continue
        existing_authors = {
            normalize_text(str(author)).casefold()
            for author in item.get("authors", [])
        }
        if existing_authors == normalized_authors:
            return True
    return False


def write_submissions(data: dict) -> None:
    SUBMITTED_FILE.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=SUBMITTED_FILE.parent,
        prefix=f".{SUBMITTED_FILE.name}.",
        delete=False,
    ) as temporary:
        temporary_path = Path(temporary.name)
        yaml.safe_dump(
            data,
            temporary,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
            width=1000,
        )
    temporary_path.replace(SUBMITTED_FILE)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Add a submitted publication to its authors' profile pages."
    )
    parser.add_argument("--date", type=parse_date, help="Submission date (YYYY-MM-DD).")
    parser.add_argument(
        "--tags",
        help="Comma-separated research-group tags, e.g. MatCat-KT.",
    )
    args = parser.parse_args(argv)

    print("Add submitted publication")
    title = prompt_value("Title")
    while not title:
        print("Title is required.", file=sys.stderr)
        title = prompt_value("Title")
    authors = prompt_authors()
    members = load_members()
    profile_ids = resolve_profile_ids(authors, members)
    try:
        tags = parse_group_tags(args.tags) if args.tags is not None else prompt_group_tags()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    default_date = args.date or date.today()
    while True:
        raw_date = prompt_value("Date (YYYY-MM-DD)", default_date.isoformat())
        try:
            submitted_date = parse_date(raw_date)
            break
        except argparse.ArgumentTypeError as exc:
            print(str(exc), file=sys.stderr)

    data = load_submissions()
    if submission_exists(data, title, authors):
        print("This submitted publication is already in the data file.", file=sys.stderr)
        return 1

    base_id = f"submitted-{submitted_date.isoformat()}-{slugify(title)}"
    existing_ids = {str(item.get("id", "")) for item in data["items"]}
    entry_id = base_id
    suffix = 2
    while entry_id in existing_ids:
        entry_id = f"{base_id}-{suffix}"
        suffix += 1

    entry = {
        "id": entry_id,
        "status": "submitted",
        "title": title,
        "authors": authors,
        "date": submitted_date.isoformat(),
        "profile_ids": profile_ids,
        "tags": tags,
    }

    print("\n=== Submitted publication ===")
    print(f"Title:   {title}")
    print(f"Authors: {'; '.join(authors)}")
    print(f"Date:    {submitted_date.isoformat()}")
    print(f"Tags:    {', '.join(tags) if tags else 'None'}")
    profile_names = [
        str(member["name"])
        for member in members
        if member["id"] in profile_ids
    ]
    print(f"Profiles: {'; '.join(profile_names) if profile_names else 'None'}")
    print("=============================\n")
    if input("Save this entry? [Y/n]: ").strip().lower() in {"n", "no"}:
        print("Cancelled; no changes written.")
        return 0

    data["items"].append(entry)
    write_submissions(data)
    print(f"Added submitted publication to {SUBMITTED_FILE}")
    print("The entry will appear on the profile pages of the listed authors.")
    print("Run 'make build && make deploy' to publish the changes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
