#!/usr/bin/env python3
"""Add local photos to the gallery and keep events sorted by title date.

Usage:
    python3 scripts/add_gallery.py "Group dinner (17.09.2026)" photos/*.jpg
    python3 scripts/add_gallery.py "Group dinner (17.09.2026)" photos/
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import yaml

from import_gallery import DATA_PATH, IMAGE_DIR, slugify, sort_events, write_yaml


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def image_sources(sources: list[Path]) -> list[Path]:
    files: list[Path] = []
    for source in sources:
        if source.is_dir():
            files.extend(
                path
                for path in sorted(source.iterdir())
                if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
            )
        elif source.is_file():
            if source.suffix.lower() not in IMAGE_SUFFIXES:
                raise ValueError(f"Not a supported image file: {source}")
            files.append(source)
        else:
            raise FileNotFoundError(f"Image or directory not found: {source}")
    if not files:
        raise ValueError("No images found")
    return files


def find_or_create_event(events: list[dict[str, object]], title: str) -> dict[str, object]:
    event_slug = slugify(title)
    for event in events:
        if str(event.get("title", "")) == title or str(event.get("slug", "")) == event_slug:
            return event

    used_slugs = {str(event.get("slug", "")) for event in events}
    unique_slug = event_slug
    suffix = 2
    while unique_slug in used_slugs:
        unique_slug = f"{event_slug}-{suffix}"
        suffix += 1
    event = {"title": title, "slug": unique_slug, "images": []}
    events.append(event)
    return event


def add_images(event: dict[str, object], sources: list[Path], dry_run: bool) -> int:
    event_slug = str(event["slug"])
    images = event.setdefault("images", [])
    if not isinstance(images, list):
        raise ValueError(f"Invalid images list for event {event_slug}")

    target_dir = IMAGE_DIR / event_slug
    existing_names = {Path(str(image.get("src", ""))).name for image in images if isinstance(image, dict)}
    added = 0
    for source in sources:
        image_number = len(images) + 1
        target_name = f"{image_number:02d}-{slugify(source.stem)}{source.suffix.lower()}"
        while target_name in existing_names:
            image_number += 1
            target_name = f"{image_number:02d}-{slugify(source.stem)}{source.suffix.lower()}"
        target = target_dir / target_name
        if not dry_run:
            target_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        images.append({"src": f"/images/gallery/{event_slug}/{target_name}", "alt": str(event["title"])})
        existing_names.add(target_name)
        added += 1
    return added


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("title", help="Gallery event title, including its date")
    parser.add_argument("sources", nargs="+", type=Path, help="Image files or directories")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without copying or writing")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sources = image_sources(args.sources)
    payload = yaml.safe_load(DATA_PATH.read_text(encoding="utf-8")) or {"items": []}
    events = payload.get("items", [])
    if not isinstance(events, list):
        raise ValueError(f"Expected a list at items in {DATA_PATH}")

    event = find_or_create_event(events, args.title)
    added = add_images(event, sources, args.dry_run)
    sorted_events = sort_events(events)

    if not args.dry_run:
        write_yaml(sorted_events)

    action = "Would add" if args.dry_run else "Added"
    print(f"{action} {added} image(s) to: {args.title}")
    print(f"Gallery events: {len(sorted_events)}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (FileNotFoundError, ValueError, yaml.YAMLError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
