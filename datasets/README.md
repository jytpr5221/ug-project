# Datasets

Two datasets for the UG project on financial misinformation detection.

| Path | Dataset | Source |
|---|---|---|
| `finfact.json` | Fin-Fact — 3,369 fact-check records | Rangapur, Wang, Shu: *Fin-Fact: A Benchmark Dataset for Multimodal Financial Fact Checking and Explanation Generation*, KDD 2024 (arXiv:2309.08793) |
| `RFC-Bench-Dataset/` | RFC-Bench — 1,123 released instances | Jiang et al.: *All That Glisters Is Not Gold: A Benchmark for Reference-Free Counterfactual Financial Misinformation Detection*, ACL 2026 long paper (`2026.acl-long.492`) |

`finfact.json` here is a copy of the file at the project root (the original was left untouched).

## 1. finfact.json — Fin-Fact

**Provenance (verified by hash).** This copy is byte-identical to the official GitHub release
`IIT-DM/Fin-Fact`, branch `FinFact` — sha256 `5e36d32a0e0149f5d86b1f81ab6fd85144136cb7975374364060f8fcf43629fd`,
29,972,446 bytes.

⚠️ The HuggingFace mirror (`amanrangapur/Fin-Fact`) is **not** the same file: it renames the `NEI`
label to `neutral` (611 records) and contains revised justification/evidence text (1,400+ records).
Do not mix the two copies in one experiment.

Records come from Snopes (2,623) and PolitiFact (746) fact checks, posted between 1995-10-19 and
2024-03-06. Labels: `true` 1,275 / `false` 1,492 / `NEI` 602.

| Field | Type | Description | Notes |
|---|---|---|---|
| `url` | str | Source fact-check page | 2,662 unique; 322 URLs are shared by 2+ records |
| `claim` | str | The claim being checked | Unique per record; 6–376 chars |
| `author` | str | Fact-check author | |
| `posted` | str | Publication date, `MM/DD/YYYY` | All parseable |
| `sci_digest` | list[str] | 0–4 short summary snippets | Empty in 708 records; items can contain several merged sentences (split artifacts) |
| `justification` | str | Full fact-check body | Median ≈ 4,500 chars; empty in 2 records (idx 2318, 2319 — both `true`, PolitiFact) |
| `issues` | list[str] | Topic tags | 163 distinct values, casing not normalized (`Economy` vs `economy`, `Taxes` vs `taxes`) |
| `image_data` | list[dict] | `{image_src, image_caption?}` per image | 4,285 images; 4,140 are Google Drive links (not bundled — must be fetched, may be unavailable); only 210 captions; 840 records have none |
| `evidence` | list[dict] | `{sentence, hrefs[]}` per annotated sentence | 18,357 sentences, 26,952 links; empty in 101 records |
| `label` | str | `true` / `false` / `NEI` | |
| `visualization_bias` | int | Present in only **17** of 3,369 records | Intended schema field, but sparsely labeled |

**Project note.** Paper 1 (`2026.findings-acl.479`) builds its English subset from Fin-Fact's Snopes
portion: 502 finance items were screened down to 144 global English items (121 false / 23 true),
then machine-translated into Chinese, Greek, and Bengali for MFMDScen.

**Quirks to watch**
- 322 URLs carry multiple (707 total) paraphrased variants of the same claim — e.g. nine rewrites of
  the “banks must report $600 transactions” claim. Use URL-/claim-group-aware train/test splits to
  avoid leakage.
- Images live behind external URLs (mostly Google Drive), not in the JSON.

## 2. RFC-Bench-Dataset/ — RFC-Bench

**Provenance.** Downloaded from HuggingFace `CarolynJiang/RFC-Bench-Dataset` (revision
`652206acc10c313dde498e574dea037fa4a20902`, last modified 2026-01-09); every file's byte size was
verified against the HF API after download. The paper is by Yuechen Jiang et al. (ACL 2026 long,
`2026.acl-long.492`); the group's umbrella project repo is https://github.com/lzw108/FMD.
License: MIT; academic research use only (no original Yahoo Finance text is redistributed).

**Contents** (data row counts read with a proper CSV parser — the `Perturbed` column contains
embedded newlines, so `wc -l` overcounts):

| File | Instances | Columns |
|---|---|---|
| `gold-label-set/causal_gold_label-1.csv` | 188 | Ticker, Date, Link, Perturbed |
| `gold-label-set/flipping_gold_label-1.csv` | 306 | Ticker, Date, Link, Perturbed |
| `gold-label-set/numerical_gold_label-1.csv` | 353 | Ticker, Date, Link, Perturbed |
| `gold-label-set/sentiment_gold_label-1.csv` | 153 | Ticker, Date, Link, Perturbed |
| `hard-case-set/causal_hard_case.csv` | 43 | Ticker, **Title**, Link, perturbed |
| `hard-case-set/flipping_hard_case.csv` | 7 | Ticker, Date, Link, Perturbed |
| `hard-case-set/numerical_hard_case.csv` | 20 | Ticker, Date, Link, Perturbed |
| `hard-case-set/sentiment_hard_case.csv` | 53 | Ticker, Date, Link, Perturbed |

Totals: 1,000 gold-label instances + 123 hard cases. Each row pairs a public Yahoo Finance article
(`Link` + `Ticker`/`Date` metadata) with a synthetic counterfactual rewrite (`Perturbed`).

⚠️ **Partial release**: the paper reports 1,826 main Benchmark instances; the current public release
contains a 1,000-instance gold subset (the `readme.md` files say more will be released). The
hard-case subset is fully released. Rows are one perturbation per source article; the original
article text is **not** redistributed, only `Link` + rewrite.
