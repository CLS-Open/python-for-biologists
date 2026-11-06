# Practical 01 — Build the environment, prove it, produce a report

**Module:** 1 · **Level:** L2 (guided) · **Time:** 45–60 min · **Dataset:** `datasets/sample/gene_family_cycs.fasta`

## Aim

Produce a self-contained quality-control report for one real data file from a
fresh environment, and prove that the environment — not luck — is what produced it.

## Instructions

1. **Make a working directory outside the course repository** so you can prove the
   install is not relying on the repository being your current directory:

   ```bash
   mkdir -p ~/p01 && cd ~/p01
   python3 -m venv .venv && source .venv/bin/activate
   python --version > environment.txt
   which python >> environment.txt
   ```

2. **Prove isolation.** Before installing anything, run:

   ```bash
   python -c "import seqreport" ; echo "exit=$?"
   ```

   Record the result. It *must* fail (`ModuleNotFoundError`, exit code 1). If it
   succeeds, you are not in the environment you think you are in — fix that first.

3. **Install from the repository**, using the editable form so you can see the
   difference later:

   ```bash
   cd /path/to/python-for-biologists
   python -m pip install -e ".[dev]"
   cd ~/p01
   seqreport --version | tee -a environment.txt
   python -c "import seqreport, sys; print(seqreport.__file__)" | tee -a environment.txt
   ```

   The last line must point inside the repository's `src/` directory, not into
   `site-packages`. That is what `-e` means.

4. **Run the tool on the real data and capture the exit code:**

   ```bash
   seqreport stats /path/to/python-for-biologists/datasets/sample/gene_family_cycs.fasta \
     | tee stats.txt
   echo "exit=$?" | tee -a environment.txt
   ```

5. **Measure something.** From `stats.txt`, report: number of records, the shortest
   and longest protein, and the mass of the human entry. Do not guess — the numbers
   are in the file you just wrote.

6. **Produce the report in all three formats:**

   ```bash
   seqreport report /path/to/python-for-biologists/datasets/sample/qc_problems.fasta \
     --out report.html
   seqreport report /path/to/python-for-biologists/datasets/sample/qc_problems.fasta \
     --out report.md
   seqreport report /path/to/python-for-biologists/datasets/sample/qc_problems.fasta \
     --out report.json
   ```

7. **Check the HTML opens offline.** Disconnect from the network (or open it on a
   machine with no network) and confirm the page renders completely, with styling
   and no missing images.

8. **Break it deliberately.** Run `seqreport qc` on a text file you create yourself
   containing `hello` and nothing else. Record the exit code and the message, and
   write one sentence explaining why that is exit code 2 and not 1.

## Deliverables

```text
p01/
├── environment.txt      # python version, which python, seqreport version, module path, exit codes
├── stats.txt            # the stats table, unedited
├── report.html          # self-contained report
├── report.md
├── report.json
└── answers.md           # the measurements from step 5 and the sentence from step 8
```

## Rubric (10 points)

| Criterion | Points | What earns full marks |
|---|---|---|
| Step 2 evidence: import fails before install | 2 | Pasted output showing `ModuleNotFoundError` and exit code 1 |
| Environment log is complete and honest | 2 | Python version, interpreter path, package path, tool version, all four present |
| Measurements match the captured output | 2 | The three numbers in `answers.md` can be found in `stats.txt` |
| Report artefacts valid | 2 | HTML has no external references; JSON parses; Markdown tables render |
| Explanation of exit code 2 | 2 | Distinguishes "cannot read the input" from "the data has errors", in one sentence |

## Common wrong answers (instructor note)

1. **"It worked, so isolation works."** Importing before installing failed — good.
   But the common error is running step 3 while `cd`'d into the repository and then
   claiming the install works: with a `src/` layout the import only succeeds if the
   package really was installed, so do the check from *outside* the repository —
   which is why step 1 moves you out of it first.
2. **Reporting "GC content" for a protein.** The stats table prints `—`. Learners
   sometimes copy the dash as `0` or omit the column. Neither is a measurement.
3. **Exit code 1 for the `hello` file.** A file that contains no FASTA header is
   not "data with errors", it is "not a FASTA file": the tool cannot start, so it
   returns 2. If a learner argues for 1, the discussion is worth having — the
   distinction is a design choice, and the design rationale is in Module 1 §4.

## Extension

Install the package into a *second* environment without `-e` (`pip install .`) and
demonstrate that editing `src/seqreport/composition.py` no longer changes behaviour
until you reinstall. Write two sentences on which mode you would recommend to a
collaborator and why.
