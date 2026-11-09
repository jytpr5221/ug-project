---
license: mit
task_categories:
- text-classification
language:
- en
tags:
- Finance
- Misinformation
pretty_name: BFC-Bench
size_categories:
- 1K<n<10K
---
## Dataset Description

RFC-Bench is a research benchmark for evaluating large language models on **reference-free counterfactual financial misinformation detection** at the paragraph level. The dataset contains only **synthetic, human-reviewed counterfactual rewrites** and **metadata** (ticker, date, and public URL) derived from publicly accessible Yahoo Finance articles; it does **not** redistribute any original news content.

All data concern **corporate-level financial narratives** and contain no personal or sensitive information. The dataset is released **for academic research only** and must not be used for investment advice, real-world financial communication, or commercial purposes.

The release includes a main benchmark (1,826 instances) and a hard-case subset (122 instances).

### Citation

```bibtex
@article{jiang2026rfcbench,
  title   = {All That Glisters Is Not Gold: A Benchmark for Reference-Free Counterfactual Financial Misinformation Detection},
  author  = {Jiang, Yuechen and Liu, Zhiwei and Cao, Yupeng and He, Yueru and Xu, Ziyang and Xu, Chen and Deng, Zhiyang and Tiwari, Prayag and Chen, Xi and Lopez-Lira, Alejandro and Huang, Jimin and Tsujii, Junichi and Ananiadou, Sophia},
  journal = {arXiv},
  year    = {2026},
  eprint  = {2601.04160},
  url     = {https://arxiv.org/abs/2601.04160}
}
```