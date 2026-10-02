#!/usr/bin/env python3
"""Validate structured site data and references to canonical group keys."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

from group_metadata import CONTENT_DIR, ROOT, load_front_matter, load_groups


DATA_DIR = ROOT / "data"
PEOPLE_DIR = CONTENT_DIR / "people"
PUBLICATION_DIR = DATA_DIR / "publications" / "years"


def validate_yaml_files() -> list[str]:
    errors: list[str] = []
    for path in sorted(DATA_DIR.rglob("*.yaml")):
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as error:
            errors.append(f"{path}: invalid YAML: {error}")
    return errors


def validate_group_references() -> list[str]:
    errors: list[str] = []
    groups = load_groups()
    known_group_keys = set(groups)

    for path in sorted(PEOPLE_DIR.glob("*.md")):
        metadata = load_front_matter(path)
        member_groups = metadata.get("groups", [])
        if not isinstance(member_groups, list):
            errors.append(f"{path}: groups must be a list")
            continue
        unknown = sorted(str(group) for group in member_groups if str(group) not in known_group_keys)
        if unknown:
            errors.append(f"{path}: unknown group key(s): {', '.join(unknown)}")

    for path in sorted(PUBLICATION_DIR.glob("*.yaml")):
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        items = payload.get("items", [])
        if not isinstance(items, list):
            errors.append(f"{path}: items must be a list")
            continue
        for index, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                errors.append(f"{path}: item {index} must be a mapping")
                continue
            item_groups = item.get("groups", [])
            if item_groups is None:
                continue
            if not isinstance(item_groups, list):
                errors.append(f"{path}: item {index} groups must be a list")
                continue
            unknown = sorted(str(group) for group in item_groups if str(group) not in known_group_keys)
            if unknown:
                errors.append(
                    f"{path}: item {index} has unknown group key(s): {', '.join(unknown)}"
                )
    return errors


def main() -> int:
    errors = [*validate_yaml_files(), *validate_group_references()]
    if errors:
        print("Site-data validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Site-data validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
