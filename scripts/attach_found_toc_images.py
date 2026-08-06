#!/usr/bin/env python3
"""Scan static/images/publications/toc and attach matching toc_image paths to generated research pages.

Additionally, if a toc file follows the naming convention <slug>-<doi-sanitized>.<ext>
and the corresponding research page does not list the DOI, attempt to reconstruct the DOI,
fetch metadata from Crossref and add the publication entry (including toc_image) to the
research page's `publications` list.
"""
from pathlib import Path
import re
import yaml
import urllib.request
import urllib.parse
import ssl
import json
import time

ROOT = Path(__file__).resolve().parents[1]
STATIC_TOC = ROOT / "static" / "images" / "publications" / "toc"
CONTENT_RESEARCH = ROOT / "content" / "matcat" / "research"
USER_AGENT = "kt-hugoblox-prototype/1.0 (attach_found_toc_images)"


def norm(s: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


def fetch_crossref_record(doi: str) -> dict | None:
    doi = doi.strip()
    if not doi:
        return None
    api = f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='')}"
    req = urllib.request.Request(api, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            payload = resp.read()
            obj = json.loads(payload)
            return obj.get("message")
    except Exception as exc:
        print(f"Warning: failed to fetch Crossref for {doi}: {exc}")
        return None


def build_publication_entry_from_crossref(message: dict) -> dict:
    def first_title(msg):
        titles = msg.get("title") or []
        return str(titles[0]) if titles else ""

    def extract_authors(msg):
        out = []
        for a in (msg.get("author") or []):
            given = a.get("given") or ""
            family = a.get("family") or ""
            name = (given + " " + family).strip()
            if name:
                out.append(name)
        return out

    doi = message.get("DOI") or ""
    title = first_title(message)
    authors = extract_authors(message)
    year = None
    for key in ("published-print", "published-online", "issued", "created"):
        val = message.get(key) or {}
        parts = val.get("date-parts") or []
        if parts and parts[0]:
            try:
                year = int(parts[0][0])
            except Exception:
                year = None
            break
    journal = (message.get("container-title") or [""])[0]
    volume = message.get("volume") or ""
    issue = message.get("issue") or ""
    pages = message.get("page") or message.get("article-number") or ""

    pub = {
        "doi": doi,
        "title": title,
        "authors": authors,
        "year": year,
        "journal": journal,
        "volume": volume,
        "issue": issue,
        "pages": pages,
    }
    return pub


# build list of available files
files = list(STATIC_TOC.glob('*'))
file_names = [f.name for f in files]
print(f"Found {len(file_names)} toc files in {STATIC_TOC}")

updated = []
for md in CONTENT_RESEARCH.glob('*/_index.md'):
    text = md.read_text(encoding='utf-8')
    if not text.startswith('---'):
        continue
    parts = text.split('---', 2)
    fm = yaml.safe_load(parts[1]) or {}
    pubs = fm.get('publications') or []
    changed = False

    # First: attach images to existing publications (existing behavior)
    for p in pubs:
        doi = (p.get('doi') or '').strip()
        if not doi:
            continue
        if p.get('toc_image'):
            continue
        # build candidates
        cand = []
        doi_lower = doi.lower()
        cand.append(norm(doi_lower))
        if '/' in doi_lower:
            after = doi_lower.split('/',1)[1]
            cand.append(norm(after))
            # strip leading single-letter prefix like 'j.' -> remove leading 'j-'
            cand.append(re.sub(r'^[a-z]-','', norm(after)))
        # also try last segment after '.' and after '/'
        last = re.split(r'[/.]', doi_lower)[-1]
        cand.append(norm(last))
        # try variations without the '10' prefix
        cand.append(norm(doi_lower.replace('10.', '')))

        matched = None
        for fname in file_names:
            fbase = Path(fname).stem.lower()
            for c in cand:
                if not c:
                    continue
                if c in fbase:
                    matched = fname
                    break
            if matched:
                break
        if matched:
            p['toc_image'] = f"/images/publications/toc/{matched}"
            p['toc_from_auto'] = True
            changed = True
            print(f"Added toc_image for DOI {doi} in {md}: {matched}")

    # Second: detect files that look like they belong to this research line (by slug prefix)
    # and add a publication entry if the DOI is not already present.
    slug_dir = md.parent
    slug = slug_dir.name
    existing_dois = { (p.get('doi') or '').lower() for p in pubs if isinstance(p, dict) and p.get('doi') }

    for fname in file_names:
        stem = Path(fname).stem
        # Expect files named like <slug>-<doi-sanitized> (safe_filename used during download)
        if not stem.startswith(slug + '-'):
            continue
        rest = stem[len(slug) + 1:]
        if not rest:
            continue
        # Try to reconstruct DOI from rest tokens: 10-XXXX-... -> 10.XXXX/rest
        tokens = rest.split('-')
        doi_candidate = None
        if len(tokens) >= 3 and tokens[0] == '10':
            doi_candidate = tokens[0] + '.' + tokens[1] + '/' + '-'.join(tokens[2:])
        elif rest.startswith('10'):
            # fallback: treat rest as doi with dots replaced by '-'
            doi_candidate = rest.replace('-', '/')
        if not doi_candidate:
            continue
        doi_lower = doi_candidate.lower()
        if doi_lower in existing_dois:
            continue
        # Add publication by fetching Crossref (best-effort) and attach toc_image
        print(f"Found toc file {fname} for slug {slug}; attempting to add DOI {doi_candidate}")
        msg = fetch_crossref_record(doi_candidate)
        if msg:
            new_pub = build_publication_entry_from_crossref(msg)
        else:
            # minimal fallback entry
            new_pub = { 'doi': doi_candidate, 'title': doi_candidate }
        new_pub['toc_image'] = f"/images/publications/toc/{fname}"
        new_pub['toc_from_auto'] = True
        pubs.insert(0, new_pub)
        changed = True
        existing_dois.add(doi_lower)
        print(f"Added publication for DOI {doi_candidate} to {md}")

    if changed:
        fm['publications'] = pubs
        new_fm = '---\n' + yaml.safe_dump(fm, sort_keys=False, allow_unicode=True) + '---\n\n'
        # preserve existing body
        body = parts[2] if len(parts) > 2 else ""
        md.write_text(new_fm + body, encoding='utf-8')
        updated.append(str(md))

print(f"Updated {len(updated)} files")
