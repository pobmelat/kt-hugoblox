# KT HugoBlox Prototype

This folder contains a Hugo-based migration scaffold focused on structure first.

The goal of this first pass is to validate:

- the main site information architecture
- a shared header for the general site
- two subgroup header variants for `matcat` and `isom`
- a clean separation between global navigation and subgroup navigation

What is included:

- a general site header with utility links plus the main research-group menu
- subgroup sections at `/matcat/` and `/isom/`
- inherited subgroup branding and menus for subgroup child pages
- placeholder pages for the top-level site areas that currently exist in WordPress
- a responsive menu ready to keep iterating

What is not included yet:

- the official HugoBlox theme dependency
- publication import
- member profiles and ACF field migration
- galleries and media migration

Why this structure still helps for HugoBlox

- Content already lives in Hugo-friendly files under `content/`
- subgroup landing pages are modeled as sections, which maps well to HugoBlox landing pages
- navigation is externalized in `data/navigation/`
- header behavior is isolated in reusable partials

Main folders

- `content/`: site pages and subgroup sections
- `data/navigation/`: shared and subgroup-specific menus
- `layouts/`: base layout and reusable partials
- `assets/`: shared CSS and JS
- `static/images/`: copied logo asset from the current WordPress child theme

Suggested next migration steps

1. Replace placeholder page bodies with migrated content from WordPress.
2. Decide whether the final implementation will stay custom Hugo or be layered onto HugoBlox blocks.
3. Migrate members into structured content files.
4. Migrate publications from BibTeX or the current WordPress source of truth.
5. Add multilingual support if needed.
