# Installation

**Time:** 10 minutes · **Ends with:** `seqreport --version` printing `seqreport 0.1.0`

## What you need

- Python **3.10 or newer** (`python3 --version` to check).
- About 100 MB of disk for the environment, and under 1 MB for the repository's data.
- On Windows: **WSL2** (Ubuntu), because Modules 1–3 assume Unix paths and a POSIX shell
  in a few places. Native Windows mostly works; when it does not, it fails in ways that
  are not worth debugging in a beginner course.

## 1. Get the code

```bash
git clone https://github.com/cls-open/python-for-biologists.git
cd python-for-biologists
```

No git? Download the ZIP from the repository page and unzip it; everything else is the
same.

## 2. Create an isolated environment

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Your prompt should change to show `(.venv)`. If it does not, the environment is not
active and everything after this will install into the wrong place.

## 3. Install the package

```bash
python -m pip install -e ".[dev]"
```

`-e` installs the package in **editable** mode: the source directory is linked into the
environment, so edits to `src/seqreport/*.py` take effect immediately. `[dev]` adds the
test and plotting tools.

## 4. Verify

```bash
seqreport --version        # seqreport 0.1.0
python -m pytest -q        # expect: 230 passed
```

Both must succeed before you start Module 1. If `pytest` reports a different number of
tests, you are not on v0.1.0 — check `git log -1`.

## 5. Optional: cross-validation and notebooks

```bash
python -m pip install biopython jupytext nbclient
python scripts/validate_against_biopython.py   # 356 comparisons, all must agree
jupyter lab notebooks/01_quality_control.ipynb
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `seqreport: command not found` | Environment not active, or install went elsewhere | `which python` must be inside `.venv`; re-run step 3 |
| `error: externally-managed-environment` | Your OS protects the system Python | That is correct behaviour — use the venv |
| `ModuleNotFoundError: seqreport` in a notebook | Notebook kernel ≠ your venv | Register it: `python -m ipykernel install --user --name seqreport` |
| `python: command not found` | Only `python3` is installed | `python3 -m venv .venv` then activate; `python` exists inside the venv |
| Tests fail on a locale error | Non-UTF-8 locale | `export PYTHONUTF8=1` |
| Slow install behind a proxy | pip cannot reach PyPI | `python -m pip install -e ".[dev]" --proxy http://your.proxy:8080` |

## Uninstall

```bash
deactivate
rm -rf .venv
```

The repository itself is untouched by this, which is the point of an environment.
