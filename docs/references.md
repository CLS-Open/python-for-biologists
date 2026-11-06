# References

Every reference below was verified on **2026-11-06** by resolving its DOI through the
Crossref API and comparing the returned title with the title claimed here. The check is
automated (`python scripts/check_references.py`) and runs in CI, because a fabricated or
drifted citation is the failure mode this page exists to prevent.

## Cited in the modules

| # | Reference | Cited in |
|---|---|---|
| R1 | Sandve GK, Nekrutenko A, Taylor J, Hovig E. **Ten Simple Rules for Reproducible Computational Research.** *PLoS Comput Biol* 9(10):e1003285, 2013. [10.1371/journal.pcbi.1003285](https://doi.org/10.1371/journal.pcbi.1003285) | Module 1 §1, §11 |
| R2 | Wilson G, Aruliah DA, Brown CT, et al. **Best Practices for Scientific Computing.** *PLoS Biol* 12(1):e1001745, 2014. [10.1371/journal.pbio.1001745](https://doi.org/10.1371/journal.pbio.1001745) | Module 1, Module 3 |
| R3 | Rule A, Birmingham A, Zuniga C, et al. **Ten simple rules for writing and sharing computational analyses in Jupyter Notebooks.** *PLoS Comput Biol* 15(7):e1007007, 2019. [10.1371/journal.pcbi.1007007](https://doi.org/10.1371/journal.pcbi.1007007) | Module 1 §1 |
| R4 | Lee BD. **Ten simple rules for documenting scientific software.** *PLoS Comput Biol* 14(12):e1006561, 2018. [10.1371/journal.pcbi.1006561](https://doi.org/10.1371/journal.pcbi.1006561) | Module 1, Module 3 |
| R5 | Beaulieu-Jones BK, Greene CS. **Reproducibility of computational workflows is automated using continuous analysis.** *Nat Biotechnol* 35:342–346, 2017. [10.1038/nbt.3780](https://doi.org/10.1038/nbt.3780) | Module 3 §11, CI design |
| R6 | Cock PJA, Antao T, Chang JT, et al. **Biopython: freely available Python tools for computational molecular biology and bioinformatics.** *Bioinformatics* 25(11):1422–1423, 2009. [10.1093/bioinformatics/btp163](https://doi.org/10.1093/bioinformatics/btp163) | Module 2, validation |
| R7 | NC-IUB. **Nomenclature for incompletely specified bases in nucleic acid sequences: recommendations 1984.** *Nucleic Acids Res* 13(9):3021–3030, 1985. [10.1093/nar/13.9.3021](https://doi.org/10.1093/nar/13.9.3021) | Module 2 (ambiguity codes) |
| R8 | Rougier NP, Droettboom M, Bourne PE. **Ten Simple Rules for Better Figures.** *PLoS Comput Biol* 10(9):e1003833, 2014. [10.1371/journal.pcbi.1003833](https://doi.org/10.1371/journal.pcbi.1003833) | Assignment 02 (figure standards) |

## Data sources

| Source | Use | Licence |
|---|---|---|
| The UniProt Consortium. **UniProt Knowledgebase (UniProtKB/Swiss-Prot).** <https://www.uniprot.org> — accessed 2026-11-06 | all sequences in `datasets/sample/` | CC BY 4.0 |
| INSDC. **Feature Table Definition.** <https://www.insdc.org/submitting-standards/feature-table/> — accessed 2026-11-06 | ambiguity-code semantics | public specification |

## Software referenced

| Software | Version used for validation | Licence |
|---|---|---|
| Python | 3.10–3.13 (CI matrix) | PSF |
| Biopython | 1.88 | BSD-3-Clause |
| Matplotlib | ≥3.8 | PSF-based |
| pytest | ≥8 | MIT |

## How to cite this repository

See [`CITATION.cff`](https://github.com/cls-open/python-for-biologists/blob/main/CITATION.cff).
Citing this course is **never** required to use or teach from the material, and no
learner is asked to cite it as a condition of participation.
