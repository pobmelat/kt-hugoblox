#!/usr/bin/env python3
from __future__ import annotations

import html
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_URL = "https://www.ehu.eus/chemistry/theory/8_gallery/donostia-quantum-chemistry-group/"
HTML_PATH = Path("/tmp/kt-gallery.html")
DATA_PATH = ROOT / "data" / "gallery.yaml"
IMAGE_DIR = ROOT / "static" / "images" / "gallery"


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii").lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "gallery"


def yaml_quote(value: str) -> str:
    value = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{value}"'


def clean_text(value: str) -> str:
    value = re.sub(r"<br\s*/?>", " ", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    value = value.replace("\u00a0", " ")
    value = value.replace("’", "'").replace("´", "'").replace("“", '"').replace("”", '"')
    value = re.sub(r"\s+", " ", value)
    return value.strip(" \t\n\r")


def get_html() -> str:
    if HTML_PATH.exists():
        return HTML_PATH.read_text(encoding="utf-8", errors="replace")
    request = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def content_body(page: str) -> str:
    match = re.search(
        r'<div class="entry-content[^"]*">(.*?)</div>\s*</article>',
        page,
        flags=re.S,
    )
    if match is None:
        raise RuntimeError("Could not find .entry-content in gallery page")
    return match.group(1)


def make_absolute(url: str) -> str:
    if url.startswith("http://") or url.startswith("https://"):
        return html.unescape(url)
    if url.startswith("/"):
        return "https://www.ehu.eus" + html.unescape(url)
    return urllib.parse.urljoin(SOURCE_URL, html.unescape(url))


def image_extension(url: str) -> str:
    suffix = Path(urllib.parse.urlparse(url).path).suffix.lower()
    return suffix if suffix in {".jpg", ".jpeg", ".png", ".webp"} else ".jpg"


def download_image(url: str, event_slug: str, index: int) -> str:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    source_name = Path(urllib.parse.unquote(urllib.parse.urlparse(url).path)).name
    stem = slugify(Path(source_name).stem)
    target_dir = IMAGE_DIR / event_slug
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{index:02d}-{stem}{image_extension(url)}"
    if target.exists() and target.stat().st_size > 1024:
        return f"/images/gallery/{event_slug}/{target.name}"

    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            content = response.read()
    except (urllib.error.URLError, TimeoutError):
        return url

    if len(content) < 1024:
        return url
    target.write_bytes(content)
    return f"/images/gallery/{event_slug}/{target.name}"


def extract_images(figure_html: str, event_slug: str, start_index: int) -> list[dict[str, object]]:
    images: list[dict[str, object]] = []
    for img_index, img_match in enumerate(re.finditer(r"<img\b([^>]*)>", figure_html, flags=re.S | re.I), start=start_index):
        attrs = img_match.group(1)
        src_match = re.search(r'\bsrc=["\']([^"\']+)["\']', attrs, flags=re.I)
        if src_match is None:
            continue
        src = make_absolute(src_match.group(1))
        alt_match = re.search(r'\balt=["\']([^"\']*)["\']', attrs, flags=re.I)
        width_match = re.search(r'\bwidth=["\']?(\d+)', attrs, flags=re.I)
        height_match = re.search(r'\bheight=["\']?(\d+)', attrs, flags=re.I)
        local_src = download_image(src, event_slug, img_index)
        image: dict[str, object] = {
            "src": local_src,
            "original_url": src,
        }
        alt = clean_text(alt_match.group(1)) if alt_match else ""
        if alt:
            image["alt"] = alt
        if width_match:
            image["width"] = int(width_match.group(1))
        if height_match:
            image["height"] = int(height_match.group(1))
        images.append(image)
    return images


def parse_gallery() -> list[dict[str, object]]:
    content = content_body(get_html())
    token_pattern = re.compile(r"(<p\b[^>]*>.*?</p>|<figure\b[^>]*>.*?</figure>)", flags=re.S | re.I)
    events: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    used_slugs: set[str] = set()

    for token in token_pattern.findall(content):
        if token.lower().startswith("<p"):
            title = clean_text(token)
            if not title:
                continue
            base_slug = slugify(title)
            event_slug = base_slug
            suffix = 2
            while event_slug in used_slugs:
                event_slug = f"{base_slug}-{suffix}"
                suffix += 1
            used_slugs.add(event_slug)
            current = {"title": title, "slug": event_slug, "images": []}
            events.append(current)
            continue

        if current is None:
            current = {"title": "Gallery", "slug": "gallery", "images": []}
            used_slugs.add("gallery")
            events.append(current)

        images = current["images"]  # type: ignore[index]
        images.extend(extract_images(token, str(current["slug"]), len(images) + 1))  # type: ignore[arg-type]

    return [event for event in events if event.get("images")]


def write_yaml(events: list[dict[str, object]]) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Generated from https://www.ehu.eus/chemistry/theory/8_gallery/donostia-quantum-chemistry-group/",
        "items:",
    ]
    for event in events:
        lines.append(f"  - title: {yaml_quote(str(event['title']))}")
        lines.append(f"    slug: {yaml_quote(str(event['slug']))}")
        lines.append("    images:")
        for image in event["images"]:  # type: ignore[index]
            lines.append(f"      - src: {yaml_quote(str(image['src']))}")
            if image.get("alt"):
                lines.append(f"        alt: {yaml_quote(str(image['alt']))}")
            if image.get("width"):
                lines.append(f"        width: {image['width']}")
            if image.get("height"):
                lines.append(f"        height: {image['height']}")
            if image.get("original_url"):
                lines.append(f"        original_url: {yaml_quote(str(image['original_url']))}")
    DATA_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    events = parse_gallery()
    write_yaml(events)
    image_count = sum(len(event["images"]) for event in events)  # type: ignore[arg-type]
    local_count = sum(
        1
        for event in events
        for image in event["images"]  # type: ignore[index]
        if str(image["src"]).startswith("/images/gallery/")
    )
    print(f"Imported {len(events)} gallery events")
    print(f"Imported {image_count} images")
    print(f"Downloaded local images: {local_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
