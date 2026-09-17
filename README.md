# Donostia Kimika Teorikoa — Hugo site

This repository contains the Hugo prototype/site for the Donostia Kimika Teorikoa (KT) research groups.

## How research groups are defined

Each group is a Hugo section under `content/<group>/`. The main source of truth for a group is its landing page:

```
content/<group>/_index.md
```

This file contains the group metadata, research lines and optional resources. The generator script reads this file and creates the per-research-line pages, the research index page and the resources page automatically.

### Minimal example: `content/biokt/_index.md`

```yaml
---
title: "Bio-KT Lab"
hide_hero: true
home_title: "Welcome to the Bio-KT Laboratory"
weight: 3
header:
  variant: "subgroup"
  menu: "biokt"
  accent: "biokt"
  brand_name: "Bio-KT Lab"
  brand_note: "Euskal Herriko Unibertsitatea & DIPC"
  brand_url: "/biokt/"
research_group_card:
  key: "biokt"
  label: "Bio-KT"
  logo: "/images/groups/biokt.png"
  summary: "Electronic structure and modelling strategies aimed at biologically relevant molecules, processes and interactions"
  leadership_label: "co-led by"
  leaders:
    - page: "/people/xabier-lopez"
      name: "Xabier Lopez"
    - page: "/people/david-de-sancho"
      name: "David de Sancho"
research_intro: false
research_lines:
  - slug: "protein-metal-interactions"
    eyebrow: "Protein Metal Interactions"
    title: "Quantum mechanics of protein-metal interactions"
    summary: "Aluminum is the third most abundant element..."
    dois:
      - "10.1039/d3cp03179a"
resources:
  title: "Software and Data Repositories"
  items:
    - name: MasterMSM
      summary: "Code for building master equation (Markov state) models of molecular kinetics."
      link: "https://github.com/daviddesancho/MasterMSM"
---

Bio-KT Laboratory operates within the Donostia Kimika Teorikoa research group...
```

### Key front-matter fields

| Field | Purpose |
|-------|---------|
| `header` | Navigation header: `menu`, `accent`, `brand_name`, `brand_url`. |
| `research_group_card` | Group card shown on the research-groups overview page. |
| `research_lines` | List of research lines. Each line becomes a page under `content/<group>/research/<slug>/`. |
| `research_intro` | Optional intro text above the grid; `false` suppresses it. |
| `resources` | Optional software/data list. Creates a `Resources` menu item and a page at `/resources/`. |

## Generating research pages

The main generator script is:

```bash
scripts/generate_research_pages.py
```

### Basic usage

Generate pages for a single group:

```bash
python3 scripts/generate_research_pages.py -g biokt
```

Regenerate everything for a group, overwriting existing pages and persisting short excerpts:

```bash
python3 scripts/generate_research_pages.py -g biokt --force --update-index --excerpt-words 4
```

Run the generator for every group that has `research_lines` or `resources`:

```bash
python3 scripts/generate_research_pages.py --all-groups --update-index --force --excerpt-words 4
```

### Common options

| Option | Meaning |
|--------|---------|
| `-g, --group <name>` | Group to process (e.g. `biokt`, `isom`, `polkt`). |
| `--all-groups` | Process every group in `content/`. |
| `--dry-run` | Preview changes without writing files. |
| `--force` | Overwrite existing research-line pages and index pages. |
| `--update-index` | Write `card_excerpt` and `card_tone` back into `content/<group>/_index.md`. |
| `--excerpt-words <n>` | Number of words used for the grid card excerpt (default: 4). |
| `--slug <slug>` | Process only one research line. |

### What the script creates

For each group it creates/updates:

- `content/<group>/research/<slug>/_index.md` — one page per research line.
- `content/<group>/research/_index.md` — the research index page (like MatCat's).
- `content/<group>/resources/_index.md` — if a `resources:` section exists.
- `data/navigation/<group>.yaml` — adds a `Resources` menu item if needed.

## TOC images for research lines

The generator tries to populate a TOC image for each publication:

1. It queries the Crossref API for each DOI listed under a research line.
2. If Crossref advertises an image link, it downloads it.
3. If not, it tries to resolve the DOI landing page and looks for `og:image`, `twitter:image`, `image_src` or other heuristic image hints.
4. Downloaded images are saved to:

   ```
   static/images/publications/toc/<safe-doi>.<ext>
   ```

Many publishers block programmatic access (HTTP 403/404), so automatic downloads often fail. If you already have a TOC image, place it in the directory above and run:

```bash
python3 scripts/attach_found_toc_images.py
```

This script scans the existing images in `static/images/publications/toc/` and attaches them to the matching publication entries by DOI. It preserves any manually added `toc_image` fields.

## Local preview and deploy

A `Makefile` is provided for common tasks. You can override any variable on the command line or in a local `.env` file.

### Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `PROD_BASEURL` | `https://www.ehu.eus/chemistry/theory/new/` | Base URL used for the production build. |
| `LFTP_USER` | `scwtcg` | SFTP username. |
| `LFTP_HOST` | `alweb.ehu.eus` | SFTP server host. |
| `REMOTE_PATH` | `/users/scwtcg/public_html/new` | Destination directory on the server. |
| `LFTP_PASS` | *(none)* | SFTP password. Provide via `.env` or environment; **never commit it**. |

### Makefile targets

```bash
# Local development server
make serve

# Production build (uses PROD_BASEURL)
make build

# Deploy the public/ folder via SFTP using lftp
make deploy

# Remove the generated public/ folder
make clean
```

### Example: deploy from scratch

```bash
# 1. Build for production
make build

# 2. Deploy (password can be set inline or in .env)
LFTP_PASS="yourpassword" make deploy
```

### Recommended `.env` file

Create a `.env` file in the repository root (it is already ignored by git):

```bash
PROD_BASEURL="https://www.ehu.eus/chemistry/theory/new/"
LFTP_USER="scwtcg"
LFTP_PASS="your-password-here"
LFTP_HOST="alweb.sw.ehu.eus"
REMOTE_PATH="/users/scwtcg/public_html/new"
```

Then simply run:

```bash
make build
make deploy
```

> **Security note:** never commit `.env` or any file containing passwords. The repository already ignores `.env`.

## Adding gallery photos

Add one or more local images to an event with:

```bash
python3 scripts/add_gallery.py "Group dinner (17.09.2026)" photos/*.jpg
```

The command also accepts directories, copies the images into
`static/images/gallery/`, updates `data/gallery.yaml`, reuses an event with
the same title, and sorts events from newest to oldest using the last date
found in each title. Use `--dry-run` to preview the operation.

## Typical workflow

1. Add or edit `content/<group>/_index.md` with research lines and/or resources.
2. Run the generator:
   ```bash
   python3 scripts/generate_research_pages.py -g <group> --update-index --force --excerpt-words 4
   ```
3. Optionally attach TOC images:
   ```bash
   python3 scripts/attach_found_toc_images.py
   ```
4. Preview locally:
   ```bash
   make serve
   ```
5. Build and deploy:
   ```bash
   make build
   make deploy
   ```

---

## Legacy prototype notes

This folder started as a Hugo-based migration scaffold focused on structure first.

- Content already lives in Hugo-friendly files under `content/`
- subgroup landing pages are modeled as sections, which maps well to HugoBlox landing pages
- navigation is externalized in `data/navigation/`
- header behavior is isolated in reusable partials
