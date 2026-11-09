# Research papers

| File | Paper | Venue |
|---|---|---|
| `2026.findings-acl.479.pdf` | **Same Claim, Different Judgment: Benchmarking Scenario-Induced Bias in Multilingual Financial Misinformation Detection** — Zhiwei Liu, Yupeng Cao, Yuechen Jiang, et al. | Findings of ACL 2026, pp. 9838–9864 |
| `2026.acl-long.492.pdf` | **All That Glisters Is Not Gold: A Benchmark for Reference-Free Counterfactual Financial Misinformation Detection** — Yuechen Jiang, Zhiwei Liu, Yupeng Cao, et al. | ACL 2026 (Long Papers), pp. 10737–10776 |

Both PDFs were downloaded from the ACL Anthology and verified against their official title pages.

- **Paper 1** introduces **MFMDScen** — scenario-induced bias benchmark for multilingual financial
  misinformation detection (English, Chinese, Greek, Bengali). Its English portion is built from the
  Snopes subset of the Fin-Fact dataset (see `../datasets/finfact.json`). Code/data:
  https://github.com/lzw108/FMD. arXiv:2601.05403.
- **Paper 2** introduces **RFC-Bench** — paragraph-level, reference-free counterfactual financial
  misinformation detection over real news (see `../datasets/RFC-Bench-Dataset/`).
  arXiv:2601.04160.

`*.bib` files are the official ACL BibTeX entries, ready to `\cite` in LaTeX:

- `2026.findings-acl.479.bib` → DOI 10.18653/v1/2026.findings-acl.479
- `2026.acl-long.492.bib` → DOI 10.18653/v1/2026.acl-long.492
