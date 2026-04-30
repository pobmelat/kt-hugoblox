#!/usr/bin/env python3

from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from difflib import SequenceMatcher
from pathlib import Path

import yaml


ROOT = Path("/Users/pobmelat/Library/CloudStorage/OneDrive-UPVEHU/Nextcloud/LANA/Web/kt-hugoblox-prototype")
YEARS_DIR = ROOT / "data" / "publications" / "years"
USER_AGENT = "kt-hugoblox-prototype/1.0 (metadata enrichment; contact local user)"


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def normalize_doi(text: str) -> str:
    text = normalize_whitespace(text)
    text = re.sub(r"^doi:\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", text, flags=re.IGNORECASE)
    return text.strip()


def normalize_title(text: str) -> str:
    text = text.lower()
    text = (
        text.replace("’", "'")
        .replace("“", '"')
        .replace("”", '"')
        .replace("–", "-")
        .replace("—", "-")
    )
    text = re.sub(r"[^a-z0-9]+", "", text)
    return text


def first_author_surname(item: dict) -> str:
    authors = item.get("authors") or []
    if not authors:
        return ""
    first = normalize_whitespace(authors[0])
    if "," in first:
        return normalize_whitespace(first.split(",", 1)[0]).lower()
    return normalize_whitespace(first.split()[-1]).lower()


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def crossref_by_doi(doi: str) -> dict | None:
    doi = normalize_doi(doi)
    if not doi:
        return None
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='')}"
    try:
        return fetch_json(url).get("message", {})
    except Exception:
        return None


def crossref_search(title: str, year: int, author_surname: str) -> list[dict]:
    query = urllib.parse.quote(title)
    filters = []
    if year:
        filters.append(f"from-pub-date:{year}-01-01")
        filters.append(f"until-pub-date:{year}-12-31")
    filter_param = ""
    if filters:
        filter_param = "&filter=" + urllib.parse.quote(",".join(filters))
    author_param = f"&query.author={urllib.parse.quote(author_surname)}" if author_surname else ""
    url = f"https://api.crossref.org/works?rows=8&query.title={query}{author_param}{filter_param}"
    try:
        data = fetch_json(url).get("message", {})
        return data.get("items", [])
    except Exception:
        return []


def candidate_score(item: dict, candidate: dict) -> tuple[float, int, int]:
    title = item.get("title", "")
    candidate_title = normalize_whitespace((candidate.get("title") or [""])[0])
    sim = SequenceMatcher(None, normalize_title(title), normalize_title(candidate_title)).ratio()
    cand_year = (
        (candidate.get("published-print") or candidate.get("published-online") or {}).get("date-parts", [[0]])[0][0]
        if candidate
        else 0
    )
    year_gap = abs(int(item.get("year", 0) or 0) - int(cand_year or 0)) if item.get("year") and cand_year else 99
    author_bonus = 0
    wanted = first_author_surname(item)
    for author in candidate.get("author", []) or []:
        family = normalize_whitespace(author.get("family", "")).lower()
        if wanted and family == wanted:
            author_bonus = 1
            break
    return sim, -year_gap, author_bonus


def pick_candidate(item: dict, candidates: list[dict]) -> dict | None:
    if not candidates:
        return None
    ranked = sorted(candidates, key=lambda cand: candidate_score(item, cand), reverse=True)
    best = ranked[0]
    sim, neg_gap, author_bonus = candidate_score(item, best)
    year_gap = -neg_gap
    if sim >= 0.98 and year_gap <= 1:
        return best
    if sim >= 0.94 and year_gap == 0 and author_bonus:
        return best
    return None


def apply_crossref_metadata(item: dict, message: dict) -> bool:
    changed = False
    doi = normalize_doi(message.get("DOI", ""))
    if doi and not item.get("doi"):
        item["doi"] = doi
        changed = True

    container = normalize_whitespace(((message.get("container-title") or [""])[0]))
    if container and not item.get("journal"):
        item["journal"] = container
        changed = True

    volume = normalize_whitespace(message.get("volume", ""))
    if volume and not item.get("volume"):
        item["volume"] = volume
        changed = True

    issue = normalize_whitespace(message.get("issue", ""))
    if issue and not item.get("issue"):
        item["issue"] = issue
        changed = True

    page = normalize_whitespace(message.get("page", ""))
    if page and not item.get("pages"):
        item["pages"] = page
        changed = True

    return changed


def load_year_files() -> list[tuple[Path, dict]]:
    loaded = []
    for path in sorted(YEARS_DIR.glob("*.yaml")):
        payload = yaml.safe_load(path.read_text()) or {}
        loaded.append((path, payload))
    return loaded


def main() -> None:
    loaded = load_year_files()
    doi_filled = 0
    journal_filled = 0
    touched_files: set[Path] = set()
    unresolved: list[str] = []

    for path, payload in loaded:
        items = payload.get("items", [])
        file_changed = False
        for item in items:
            changed = False
            had_doi = bool(item.get("doi"))
            had_journal = bool(item.get("journal"))

            if item.get("doi") and not item.get("journal"):
                message = crossref_by_doi(item["doi"])
                if message:
                    changed = apply_crossref_metadata(item, message) or changed
            elif not item.get("doi"):
                candidates = crossref_search(item.get("title", ""), int(item.get("year", 0) or 0), first_author_surname(item))
                best = pick_candidate(item, candidates)
                if best:
                    changed = apply_crossref_metadata(item, best) or changed
                else:
                    unresolved.append(f"{item.get('id')} | {item.get('title')} | {path.name}")

            if changed:
                file_changed = True
                if not had_doi and item.get("doi"):
                    doi_filled += 1
                if not had_journal and item.get("journal"):
                    journal_filled += 1
            time.sleep(0.15)

        if file_changed:
            path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, width=1000), encoding="utf-8")
            touched_files.add(path)

    print(f"Filled DOI for {doi_filled} items")
    print(f"Filled journal for {journal_filled} items")
    print(f"Touched {len(touched_files)} year files")
    print("UNRESOLVED")
    for row in unresolved:
        print(row)


if __name__ == "__main__":
    main()
