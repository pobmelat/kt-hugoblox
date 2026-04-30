#!/usr/bin/env python3

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

import yaml
from bs4 import BeautifulSoup


ROOT = Path("/Users/pobmelat/Library/CloudStorage/OneDrive-UPVEHU/Nextcloud/LANA/Web/kt-hugoblox-prototype")
WP_JSON = Path("/tmp/kt_publications_wp.json")
TAG_HTML_GLOB = "/tmp/teachpress_tag_*.html"
YEARS_DIR = ROOT / "data" / "publications" / "years"


TAG_COMPAT = {
    "MatCat-ExMat": ["MatCat-Exotic"],
    "MatCat-HetCatEl": ["MatCat-HetCatE"],
    "MatCat-KT": ["MatCat"],
}

TAG_NORMALIZE = {
    "Sus-KT": "SUS-KT",
}

TAG_TO_GROUP = {
    "Bio-KT": "biokt",
    "MatCat-KT": "matcat",
    "MatCat-ExMat": "matcat",
    "MatCat-HetCatEl": "matcat",
    "MatCat-NanoSurf": "matcat",
    "MolEles-KT": "moleles",
    "NOFT": "noft",
    "POL-KT": "polkt",
    "QCD-KT": "qcd",
}


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "publication"


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def normalize_tag(tag: str) -> str:
    tag = normalize_whitespace(tag)
    return TAG_NORMALIZE.get(tag, tag)


def normalize_doi(doi: str) -> str:
    doi = normalize_whitespace(doi)
    doi = re.sub(r"^doi:\s*", "", doi, flags=re.IGNORECASE)
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE)
    return doi.strip()


def parse_bibtex(text: str) -> tuple[str | None, dict[str, str]]:
    raw = text.replace("<br/>", "\n").replace("<br />", "\n")
    raw = raw.replace("\r", "")
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    bibkey = None
    fields: dict[str, str] = {}
    if lines:
        m = re.match(r"@[\w-]+\{([^,]+),", lines[0])
        if m:
            bibkey = m.group(1).strip()
    for line in lines[1:]:
        if line == "}":
            continue
        m = re.match(r"([A-Za-z0-9_]+)\s*=\s*\{(.*)\},?$", line)
        if m:
            fields[m.group(1).lower()] = m.group(2).strip()
    return bibkey, fields


def parse_additional(additional_node) -> tuple[str, int, str, str, str]:
    journal = ""
    year = 0
    volume = ""
    issue = ""
    pages = ""

    if additional_node is None:
        return journal, year, volume, issue, pages

    em = additional_node.find("em")
    if em:
        journal = normalize_whitespace(em.get_text(" ", strip=True))

    strong = additional_node.find("strong")
    if strong:
        try:
            year = int(normalize_whitespace(strong.get_text(" ", strip=True)))
        except ValueError:
            year = 0

    text = normalize_whitespace(additional_node.get_text(" ", strip=True))
    if journal and text.startswith(journal):
        text = text[len(journal):].lstrip(" ,")
    if strong:
        year_text = normalize_whitespace(strong.get_text(" ", strip=True))
        text = text.replace(year_text, "", 1).lstrip(" ,")

    if text:
        if "," in text:
            first, rest = text.split(",", 1)
            volume_issue = normalize_whitespace(first)
            tail = normalize_whitespace(rest).strip(", ")
        else:
            volume_issue = normalize_whitespace(text)
            tail = ""

        if volume_issue:
            m = re.match(r"(.+?)\((.+?)\)$", volume_issue)
            if m:
                volume = m.group(1).strip()
                issue = m.group(2).strip()
            else:
                volume = volume_issue

        if tail:
            pages = tail

    return journal, year, volume, issue, pages


def derive_id(doi: str, bibkey: str | None, title: str, teachpress_id: str) -> str:
    if doi:
        doi = normalize_doi(doi)
        return slugify(doi.replace("/", "-").replace(".", "-"))
    if bibkey and bibkey.lower() != "nokey":
        return slugify(bibkey)
    if title and title != "[No title]":
        return slugify(title)[:80]
    return f"teachpress-{teachpress_id}"


def load_existing_items() -> tuple[dict[str, dict], dict[str, dict]]:
    by_doi: dict[str, dict] = {}
    by_title_year: dict[str, dict] = {}
    for path in YEARS_DIR.glob("*.yaml"):
        data = yaml.safe_load(path.read_text()) or {}
        for item in data.get("items", []):
            doi = normalize_whitespace(str(item.get("doi", "")))
            if doi:
                by_doi[doi.lower()] = item
            key = f"{normalize_whitespace(item.get('title', '')).lower()}::{item.get('year', 0)}"
            if key.strip(":"):
                by_title_year[key] = item
    return by_doi, by_title_year


def parse_publications() -> tuple[dict[str, dict], dict[str, str]]:
    payload = json.loads(WP_JSON.read_text())
    html = payload["content"]["rendered"]
    soup = BeautifulSoup(html, "html.parser")

    tag_map: dict[str, str] = {}
    select = soup.select_one("select#tgid")
    if select:
        for option in select.find_all("option"):
            tag_id = option.get("value", "").strip()
            label = normalize_whitespace(option.get_text(" ", strip=True))
            if tag_id:
                tag_map[tag_id] = label

    publications: dict[str, dict] = {}
    for pub in soup.select("div.tp_publication"):
        title_link = pub.select_one("p.tp_pub_title a.tp_title_link")
        title_node = pub.select_one("p.tp_pub_title")
        if not title_node:
            continue

        teachpress_id = None
        onclick = title_link.get("onclick", "") if title_link else ""
        m = re.search(r"teachpress_pub_showhide\('(\d+)'", onclick)
        if m:
            teachpress_id = m.group(1)
        else:
            for selector in ("a[id^='tp_bibtex_sh_']", "a[id^='tp_links_sh_']", "div.tp_bibtex[id^='tp_bibtex_']"):
                node = pub.select_one(selector)
                if not node:
                    continue
                node_id = node.get("id", "")
                m = re.search(r"(\d+)$", node_id)
                if m:
                    teachpress_id = m.group(1)
                    break

        if not teachpress_id:
            continue

        title_type = title_node.select_one("span.tp_pub_type")
        if title_type:
            title_type.extract()
        title = normalize_whitespace(title_node.get_text(" ", strip=True))

        if not title:
            continue

        type_match = re.search(r"tp_publication_([a-z]+)", " ".join(pub.get("class", [])))
        pub_type = type_match.group(1).lower() if type_match else "article"

        author_text = normalize_whitespace((pub.select_one("p.tp_pub_author") or "").get_text(" ", strip=True) if pub.select_one("p.tp_pub_author") else "")
        authors = [normalize_whitespace(x) for x in author_text.split(";") if normalize_whitespace(x)]

        journal, year, volume, issue, pages = parse_additional(pub.select_one("p.tp_pub_additional"))

        bibkey = None
        bib_fields: dict[str, str] = {}
        bib_node = pub.select_one("div.tp_bibtex pre")
        if bib_node:
            bibkey, bib_fields = parse_bibtex(bib_node.decode_contents())

        if bib_fields.get("author"):
            authors = [normalize_whitespace(x) for x in bib_fields["author"].split(" and ") if normalize_whitespace(x)]

        doi = normalize_doi(bib_fields.get("doi", ""))
        if not doi:
            doi_link = pub.select_one("div.tp_links a[href*='doi']")
            if doi_link and doi_link.get("href"):
                doi = normalize_doi(doi_link["href"])

        if not year:
            try:
                year = int(bib_fields.get("year", "0"))
            except ValueError:
                year = 0

        journal = journal or normalize_whitespace(bib_fields.get("journal", ""))
        volume = volume or normalize_whitespace(bib_fields.get("volume", ""))
        issue = issue or normalize_whitespace(bib_fields.get("number", ""))
        pages = pages or normalize_whitespace(bib_fields.get("pages", ""))

        item = {
            "teachpress_id": teachpress_id,
            "bibtex_key": bibkey or "",
            "type": pub_type,
            "title": title,
            "doi": doi,
            "year": year,
            "journal": journal,
            "volume": volume,
            "issue": issue,
            "pages": pages,
            "authors": authors,
            "tags": [],
            "groups": [],
        }

        for tag_link in pub.select("p.tp_pub_menu a[href*='?tgid=']"):
            href = tag_link.get("href", "")
            m = re.search(r"[?&]tgid=(\d+)", href)
            tag_label = tag_map.get(m.group(1), "") if m else ""
            if not tag_label:
                tag_label = normalize_whitespace(tag_link.get_text(" ", strip=True))
            tag_label = normalize_tag(tag_label)
            if tag_label and tag_label not in item["tags"]:
                item["tags"].append(tag_label)

        publications[teachpress_id] = item

    return publications, tag_map


def apply_tag_memberships(publications: dict[str, dict], tag_map: dict[str, str]) -> None:
    for html_path in sorted(Path("/tmp").glob("teachpress_tag_*.html")):
        html = html_path.read_text(errors="ignore")
        soup = BeautifulSoup(html, "html.parser")
        selected = soup.select_one("select#tgid option[selected]")
        if not selected:
            continue
        tag_id = selected.get("value", "").strip()
        tag_label = tag_map.get(tag_id, normalize_whitespace(selected.get_text(" ", strip=True)))
        if not tag_label:
            continue

        for pub in soup.select("div.tp_publication"):
            title_link = pub.select_one("p.tp_pub_title a.tp_title_link")
            if not title_link:
                continue
            onclick = title_link.get("onclick", "")
            m = re.search(r"teachpress_pub_showhide\('(\d+)'", onclick)
            if not m:
                continue
            pub_id = m.group(1)
            item = publications.get(pub_id)
            if not item:
                continue
            if tag_label not in item["tags"]:
                item["tags"].append(tag_label)


def merge_existing(publications: dict[str, dict]) -> list[dict]:
    by_doi, by_title_year = load_existing_items()
    merged: list[dict] = []

    for teachpress_id, item in publications.items():
        doi_key = item["doi"].lower() if item["doi"] else ""
        title_year_key = f"{normalize_whitespace(item['title']).lower()}::{item['year']}"
        existing = by_doi.get(doi_key) or by_title_year.get(title_year_key)

        tags = [normalize_tag(tag) for tag in item["tags"]]
        for tag in list(tags):
            for alias in TAG_COMPAT.get(tag, []):
                if alias not in tags:
                    tags.append(alias)

        groups = list(item["groups"])
        for tag in tags:
            group = TAG_TO_GROUP.get(tag)
            if group and group not in groups:
                groups.append(group)

        final = {
            "id": derive_id(item["doi"], item["bibtex_key"], item["title"], teachpress_id),
            "type": item["type"],
            "title": item["title"],
            "doi": item["doi"],
            "year": item["year"],
            "journal": item["journal"],
            "volume": item["volume"],
            "issue": item["issue"],
            "pages": item["pages"],
            "groups": groups,
            "tags": tags,
            "authors": item["authors"],
        }

        if item["teachpress_id"]:
            final["teachpress_id"] = item["teachpress_id"]

        if existing:
            if existing.get("id"):
                final["id"] = existing["id"]
            for key in ("toc_image", "toc_link"):
                if existing.get(key):
                    final[key] = existing[key]
            for key in ("groups", "tags"):
                if existing.get(key):
                    for value in existing[key]:
                        if key == "tags":
                            value = normalize_tag(value)
                        if value not in final[key]:
                            final[key].append(value)

        if not final["doi"]:
            final.pop("doi", None)
        if not final["journal"]:
            final.pop("journal", None)
        if not final["volume"]:
            final.pop("volume", None)
        if not final["issue"]:
            final.pop("issue", None)
        if not final["pages"]:
            final.pop("pages", None)
        if not final["groups"]:
            final.pop("groups", None)
        if not final["tags"]:
            final.pop("tags", None)
        if not final["authors"]:
            final.pop("authors", None)

        merged.append(final)

    return merged


def item_score(item: dict) -> tuple:
    title = normalize_whitespace(item.get("title", ""))
    journal = normalize_whitespace(item.get("journal", ""))
    doi = normalize_doi(str(item.get("doi", "")))
    authors = item.get("authors") or []
    year = int(item.get("year", 0) or 0)
    return (
        0 if title == "[No title]" else 1,
        1 if year > 0 else 0,
        1 if journal else 0,
        1 if doi else 0,
        len(authors),
        len(item.get("tags", []) or []),
        len(item.get("groups", []) or []),
        len(title),
    )


def dedupe_by_doi(items: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    passthrough: list[dict] = []

    for item in items:
        doi = normalize_doi(str(item.get("doi", "")))
        if doi:
            grouped[doi.lower()].append(item)
        else:
            passthrough.append(item)

    deduped: list[dict] = []
    for doi, group in grouped.items():
        if len(group) == 1:
            deduped.append(group[0])
            continue

        keeper = max(group, key=item_score)
        for other in group:
            if other is keeper:
                continue
            for key in ("tags", "groups", "authors"):
                for value in other.get(key, []) or []:
                    if value not in keeper.setdefault(key, []):
                        keeper[key].append(value)
            for key in ("toc_image", "toc_link"):
                if not keeper.get(key) and other.get(key):
                    keeper[key] = other[key]
            if keeper.get("year", 0) in (0, None, "") and other.get("year", 0):
                keeper["year"] = other["year"]
            if (not keeper.get("journal")) and other.get("journal"):
                keeper["journal"] = other["journal"]
            if keeper.get("title") == "[No title]" and other.get("title"):
                keeper["title"] = other["title"]
            if (not keeper.get("doi")) and other.get("doi"):
                keeper["doi"] = other["doi"]
        deduped.append(keeper)

    deduped.extend(passthrough)
    return deduped


def write_year_files(items: list[dict]) -> None:
    buckets: dict[int, list[dict]] = defaultdict(list)
    for item in items:
        buckets[int(item.get("year", 0))].append(item)

    for old_path in YEARS_DIR.glob("*.yaml"):
        old_path.unlink()

    for year, year_items in buckets.items():
        year_items.sort(key=lambda item: (normalize_whitespace(item.get("title", "")).lower(), item.get("id", "")))
        payload = {"items": year_items}
        out_path = YEARS_DIR / f"{year:04d}.yaml"
        out_path.write_text(
            yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, width=1000),
            encoding="utf-8",
        )


def main() -> None:
    publications, tag_map = parse_publications()
    apply_tag_memberships(publications, tag_map)
    items = merge_existing(publications)
    items = dedupe_by_doi(items)
    write_year_files(items)

    year_count = defaultdict(int)
    tag_count = defaultdict(int)
    for item in items:
        year_count[item["year"]] += 1
        for tag in item.get("tags", []):
            tag_count[tag] += 1

    print(f"Imported {len(items)} publications")
    print(f"Years: {min(year_count)}-{max(year_count)}")
    for tag, count in sorted(tag_count.items()):
        print(f"{tag}: {count}")


if __name__ == "__main__":
    main()
