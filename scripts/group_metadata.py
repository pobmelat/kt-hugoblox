"""Read canonical research-group metadata from Hugo section landing pages."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"


@dataclass(frozen=True)
class Group:
    key: str
    label: str


def normalize_group_token(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]", "", normalized.casefold())


def load_front_matter(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    metadata = yaml.safe_load(parts[1]) or {}
    if not isinstance(metadata, dict):
        raise ValueError(f"Expected YAML front matter in {path}")
    return metadata


def load_groups() -> dict[str, Group]:
    groups: dict[str, Group] = {}
    for section in sorted(CONTENT_DIR.iterdir()):
        index = section / "_index.md"
        if not section.is_dir() or not index.is_file():
            continue
        metadata = load_front_matter(index)
        card = metadata.get("research_group_card")
        if not isinstance(card, dict):
            continue
        key = str(card.get("key") or section.name).strip()
        label = str(card.get("label") or key).strip()
        if not key or not label:
            raise ValueError(f"Group metadata requires key and label in {index}")
        if key in groups:
            raise ValueError(f"Duplicate group key '{key}' in {index}")
        groups[key] = Group(key=key, label=label)
    return groups


def group_aliases(groups: dict[str, Group]) -> dict[str, Group]:
    aliases: dict[str, Group] = {}
    for group in groups.values():
        for value in (group.key, group.label):
            token = normalize_group_token(value)
            existing = aliases.get(token)
            if existing and existing.key != group.key:
                raise ValueError(f"Group alias '{value}' is ambiguous")
            aliases[token] = group
    return aliases
