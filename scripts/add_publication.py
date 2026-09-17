#!/usr/bin/env python3
"""Add a publication to data/publications/years/YYYY.yaml from a DOI.

The script asks for:
- DOI
- group
- comma-separated tags

Then it fetches metadata from Crossref and appends the article to the
corresponding yearly YAML file used by the Hugo prototype.
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "publications" / "years"
CROSSREF_API = "https://api.crossref.org/works/"
USER_AGENT = "kt-hugoblox-prototype/1.0 (publication import helper)"


def prompt(label: str) -> str:
    return input(label).strip()


def normalize_doi(raw: str) -> str:
    value = raw.strip()
    value = re.sub(r"^https?://(dx\.)?doi\.org/", "", value, flags=re.IGNORECASE)
    value = re.sub(r"^doi:\s*", "", value, flags=re.IGNORECASE)
    return value.strip()


def looks_like_doi(value: str) -> bool:
    """Basic sanity check for a DOI string."""
    if not value:
        return False
    if " " in value or "\t" in value or "\n" in value:
        return False
    if "/" not in value:
        return False
    # Most DOIs start with 10.; allow other prefixes just in case, but warn.
    return True


def slugify(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    lowered = re.sub(r"-{2,}", "-", lowered)
    return lowered.strip("-")


def build_id(authors: list[str], year: int, title: str) -> str:
    lead = authors[0].split()[-1] if authors else "publication"
    words = re.findall(r"[A-Za-z0-9]+", title)[:4]
    title_part = "-".join(word.lower() for word in words) or "article"
    return slugify(f"{lead}-{year}-{title_part}")


def fetch_crossref_record(doi: str) -> dict:
    url = CROSSREF_API + urllib.parse.quote(doi, safe="")
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = response.read()
    data = yaml.safe_load(payload)
    if not isinstance(data, dict) or "message" not in data:
        raise RuntimeError("Unexpected Crossref response")
    return data["message"]


def extract_year(message: dict) -> int:
    for key in ("published-print", "published-online", "issued", "created"):
        value = message.get(key) or {}
        parts = value.get("date-parts") or []
        if parts and parts[0]:
            return int(parts[0][0])
    raise RuntimeError("Could not determine publication year")


def extract_pages(message: dict) -> str:
    return str(message.get("page") or message.get("article-number") or "").strip()


def extract_issue(message: dict) -> str:
    return str(message.get("issue") or "").strip()


def extract_volume(message: dict) -> str:
    return str(message.get("volume") or "").strip()


def extract_title(message: dict) -> str:
    titles = message.get("title") or []
    if not titles:
        raise RuntimeError("Crossref record has no title")
    return str(titles[0]).strip()


def extract_journal(message: dict) -> str:
    journals = message.get("container-title") or []
    return str(journals[0]).strip() if journals else ""


def extract_authors(message: dict) -> list[str]:
    authors = []
    for author in message.get("author") or []:
        given = str(author.get("given") or "").strip()
        family = str(author.get("family") or "").strip()
        full_name = " ".join(part for part in (given, family) if part).strip()
        if full_name:
            authors.append(full_name)
    return authors


def parse_tags(raw: str) -> list[str]:
    return [tag.strip() for tag in raw.split(",") if tag.strip()]


def load_year_file(path: Path) -> dict:
    if not path.exists():
        return {"items": []}
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if "items" not in data or not isinstance(data["items"], list):
        data["items"] = []
    return data


def publication_exists(doi: str) -> Path | None:
    for yaml_path in sorted(DATA_DIR.glob("*.yaml")):
        with yaml_path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        for item in data.get("items", []):
            if str(item.get("doi", "")).strip().lower() == doi.lower():
                return yaml_path
    return None


def write_year_file(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(
            data,
            handle,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
            width=1000,
        )


GROUP_LABELS = {
    "isom": "ISoM-KT",
    "matcat": "MatCat-KT",
    "biokt": "Bio-KT",
    "polkt": "Pol-KT",
    "noft": "NOFT-KT",
    "moleles": "MolEleS-KT",
    "qcd": "QCD-KT",
    "momag": "MoMag-KT",
}


def build_tags(groups: list[str], extra_tags: list[str]) -> list[str]:
    tags = [GROUP_LABELS[g] for g in groups if g in GROUP_LABELS]
    for tag in extra_tags:
        tag = tag.strip()
        if tag and tag not in tags:
            tags.append(tag)
    return tags


def build_entry(message: dict, groups: list[str], extra_tags: list[str]) -> dict:
    year = extract_year(message)
    title = extract_title(message)
    journal = extract_journal(message)
    authors = extract_authors(message)

    entry: dict = {
        "id": build_id(authors, year, title),
        "type": "article",
        "title": title,
        "doi": message.get("DOI", ""),
        "year": year,
        "journal": journal,
        "groups": groups,
        "tags": build_tags(groups, extra_tags),
        "authors": authors,
    }

    volume = extract_volume(message)
    if volume:
        entry["volume"] = volume
    issue = extract_issue(message)
    if issue:
        entry["issue"] = issue
    pages = extract_pages(message)
    if pages:
        entry["pages"] = pages

    return entry


def confirm(prompt_text: str, default: bool = True) -> bool:
    suffix = " [Y/n]: " if default else " [y/N]: "
    raw = input(f"{prompt_text}{suffix}").strip().lower()
    if raw == "":
        return default
    return raw in ("y", "yes")


def ask_doi(initial: str = "") -> str | None:
    """Ask for a DOI and validate it; loop until valid or empty."""
    doi = normalize_doi(initial) if initial else ""
    while True:
        if not doi:
            doi = normalize_doi(prompt("DOI"))
        if not doi:
            print("No DOI provided.", file=sys.stderr)
            return None

        if not looks_like_doi(doi):
            print(f"This does not look like a valid DOI: {doi}", file=sys.stderr)
            doi = ""
            continue

        if not doi.startswith("10."):
            print(f"Warning: DOI does not start with '10.': {doi}", file=sys.stderr)
            if not confirm("Continue anyway?", default=False):
                doi = ""
                continue

        return doi


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Add a publication from its DOI.")
    ap.add_argument("doi", nargs="?", help="DOI of the publication (optional)")
    args = ap.parse_args(argv)

    print("Add publication from DOI")

    doi = ask_doi(args.doi or "")
    if doi is None:
        return 1

    print(f"DOI: {doi}")

    existing = publication_exists(doi)
    if existing:
        print(f"DOI already exists in {existing}")
        return 1

    try:
        message = fetch_crossref_record(doi)
    except Exception as exc:  # pragma: no cover - runtime/network path
        print(f"Could not fetch DOI metadata: {exc}", file=sys.stderr)
        return 1

    year = extract_year(message)
    title = extract_title(message)
    journal = extract_journal(message)
    authors = extract_authors(message)

    print("\n=== Crossref metadata ===")
    print(f"Title:   {title}")
    print(f"Year:    {year}")
    print(f"Journal: {journal}")
    print(f"Authors: {'; '.join(authors)}")
    print(f"DOI:     {doi}")
    print("=========================\n")

    print(f"Available groups: {', '.join(GROUP_LABELS.keys())}")
    groups_raw = prompt("Groups (comma-separated, e.g. biokt,isom): ").lower()
    groups = [g.strip() for g in groups_raw.split(",") if g.strip()]
    invalid = [g for g in groups if g not in GROUP_LABELS]
    if invalid:
        print(f"Invalid group(s): {', '.join(invalid)}", file=sys.stderr)
        print(f"Valid groups are: {', '.join(GROUP_LABELS.keys())}", file=sys.stderr)
        return 1
    if not groups:
        print("No group provided.", file=sys.stderr)
        return 1

    extra_tags = []
    if confirm("Add extra tag IT2067?", default=True):
        extra_tags.append("IT2067")

    print(f"\nGroups: {', '.join(groups)}")
    print(f"Tags:   {', '.join(build_tags(groups, extra_tags))}")

    entry = build_entry(message, groups, extra_tags)

    year_path = DATA_DIR / f"{year}.yaml"
    data = load_year_file(year_path)
    data["items"].append(entry)
    write_year_file(year_path, data)

    print(f"\nAdded publication to {year_path}")
    print("Run 'make build && make deploy' to publish the changes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
