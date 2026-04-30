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
- Entries with missing journal: `15`
- Entries with missing DOI: `36`

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

## Remaining missing journal entries

- `Electron correlation: Quantum chemistry's holy grail` — `2003.yaml`
- `Pair densities for the Hooke and Hooke-Calogero models of the non-Born-Oppenheimer hydrogen molecule` — `2005.yaml`
- `NATURAL ORBITAL FUNCTIONAL THEORY` — `2007.yaml`
- `LASER ENERGY DEPOSITION IN NANODROPLETS AND NUCLEAR FUSION DRIVEN BY COULOMB EXPLOSION` — `2015.yaml`
- `Nanocluster-Assembled materials` — `2016.yaml`
- `Rules of Aromaticity` — `2016.yaml`
- `What Can Be Learnt from a Location of Bond Paths and from Electron Density Distribution` — `2016.yaml`
- `CONTINUOUS SYMMETRY MEASURES: A NEW TOOL IN QUANTUM CHEMISTRY` — `2017.yaml`
- `Computational Design of Clusters for Catalysis` — `2018.yaml`
- `Advances in approximate natural orbital functional theory` — `2019.yaml`
- `Learning to Model G-Quadruplexes: Current Methods and Perspectives` — `2021.yaml`
- `APOST-3D: Chemical concepts from wavefunction analysis` — `2024.yaml`
- `Biallelic variants in SNUPN cause a limb girdle muscular dystrophy with myofibrillar-like features` — `2024.yaml`
- `How many distinct and reliable multireference diagnostics are there?` — `2025.yaml`
- `Toward a formulation of a CISS theory with the inclusion of two-particle relativistic effects, electron–phonon coupling, and electron–electron correlation. An application to NMR-based chiral discrimination` — `2025.yaml`

## Remaining missing DOI entries

Examples:
- `MO STUDIES ON BETA-LACTAMS .1. ON THE STRUCTURE AND REACTIVITY OF AZETIDIN-2-ONE WITH SPLIT-VALENCE BASIS-SETS` — `1988.yaml`
- `Evaluation of screened nuclear attraction and electron repulsion molecular integrals over Gaussian basis functions` — `1997.yaml`
- `Proceedings of the International Conference on "Electronic Structure: Predictions and Applications" - Preface` — `2002.yaml`
- `Electron correlation: Quantum chemistry's holy grail` — `2003.yaml`
- `Rationalizing chemical bonding in molecular Wankel motors` — `2011.yaml`
- `Multicenter Bond Index: A versatile tool to characterize electron delocalization and aromaticity` — `2014.yaml`

## Notes

- The import script is:
  - `scripts/import_teachpress_publications.py`
- It now clears old yearly YAML files before rewriting them.
- It preserves already curated fields such as `toc_image` and `toc_link` when they already existed.
- The remaining missing fields come from the original TeachPress export itself, not from the Hugo conversion layer.
