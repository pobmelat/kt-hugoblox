# TeachPress Publications Import Audit

Source:
- `https://www.ehu.eus/chemistry/theory/5_kt-seminars/scientific-publications/`

Current import status:
- Raw TeachPress publications imported: `1011`
- Final publications after DOI deduplication: `995`
- Duplicate DOI records removed: `16`
- Year files generated: `41`
- Range: `1985` to `2026`

## Summary of current issues

- Duplicate DOI entries: `0`
- Entries with missing year: `0`
- Entries with missing title: `0`
- Entries with missing authors: `0`
- Entries with missing journal: `1`
- Entries with missing DOI: `21`

## What was fixed automatically

- All duplicate DOI entries were collapsed into a single best record.
- Bad `0000.yaml` remnants were removed during rewrite.
- For duplicate DOI cases, the importer now keeps the strongest entry and merges:
  - `tags`
  - `groups`
  - `authors`
  - `toc_image`
  - `toc_link`
- Missing `year`, `journal`, `title`, and `doi` are filled from the better duplicate when possible.

## Remaining missing journal entry

- `Pair densities for the Hooke and Hooke-Calogero models of the non-Born-Oppenheimer hydrogen molecule` — `2005.yaml`

## Remaining missing DOI entries

Examples:
- `Development of an ab initio database for biological phosphate hydrolysis` — `2001.yaml`
- `Pair densities for the Hooke and Hooke-Calogero models of the non-Born-Oppenheimer hydrogen molecule` — `2005.yaml`
- `Rationalizing chemical bonding in molecular Wankel motors` — `2011.yaml`
- `Linker effects in single molecule protein folding from molecular simulations` — `2019.yaml`
- `Anàlisi de la correlació electrònica mitjançant funcions intraculars Electronic correlation analysis using intracule functions` — `2025.yaml`
- `Metal-Insulator Transition described by NOFT` — `2025.yaml`

## Likely DOI-free records

Most of the remaining DOI-less entries look like one of these:
- ACS meeting abstracts in `Abstracts of Papers of the American Chemical Society`
- conference or prefatory records with no Crossref DOI
- local theses or society-bulletin style entries
- ambiguous title-only records where Crossref does not return a safe exact match

## Notes

- The import script is:
  - `scripts/import_teachpress_publications.py`
- The Crossref enrichment script is:
  - `scripts/enrich_publications_crossref.py`
- It now clears old yearly YAML files before rewriting them.
- It preserves already curated fields such as `toc_image` and `toc_link` when they already existed.
- The remaining missing fields mostly come from the original TeachPress export itself, not from the Hugo conversion layer.
