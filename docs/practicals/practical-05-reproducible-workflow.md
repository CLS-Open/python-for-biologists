# Practical 05 — Script → tool: a workflow someone else can re-run

**Module:** 1–3 combined · **Level:** L3 (independent) · **Time:** 90 min · **Dataset:** `datasets/sample/uniprot_human_subset.fasta`

## Aim

Turn an exploratory analysis into a three-command workflow that a stranger can
re-run on a fresh clone and get byte-identical outputs.

## Instructions

1. **Analyse first, in a notebook or REPL.** For the 60-protein subset, produce:
   - the number of records and total residues;
   - the 10 longest proteins (accession, length);
   - the mass of each record;
   - one figure: length versus mass, with both axes labelled and units stated.

   Do this messily. That is the point: you are going to convert it.

2. **Extract the logic into `analysis.py`** with a `main()` that:
   - takes the input path as an argument (no hard-coded paths);
   - writes `outputs/summary.json` and `outputs/length_vs_mass.png`;
   - prints nothing on success except one line naming the outputs;
   - returns exit code 0, or 2 on a missing/unreadable input.

3. **Make the figure deterministic.** Sort before you iterate; pass an explicit
   seed if you use any randomness; strip the library version from the PNG metadata
   (`savefig(..., metadata={"Software": None})`). Prove it:

   ```bash
   python analysis.py datasets/sample/uniprot_human_subset.fasta
   md5sum outputs/length_vs_mass.png
   PYTHONHASHSEED=7 python analysis.py datasets/sample/uniprot_human_subset.fasta
   md5sum outputs/length_vs_mass.png
   ```

   The two hashes must be identical. If they are not, find the non-determinism —
   it is almost always set/dict iteration order or a timestamp.

4. **Write `test_analysis.py`** with at least four tests: the summary numbers on the
   real file; a missing-file exit code; a malformed file; and a determinism test that
   runs the figure function twice and compares bytes.

5. **Write `README.md`** for the workflow, with exactly three commands: install, run,
   test. Nothing else. If a reader needs a fourth command, the workflow is wrong.

6. **The fresh-clone test.** Copy your directory to `/tmp`, delete `outputs/` and any
   `.venv`, and run your three commands. Record the transcript in `transcript.txt`.
   Anything you had to do that is *not* in the README is a defect in the README.

## Deliverables

```text
p05/
├── analysis.py
├── test_analysis.py
├── README.md
├── transcript.txt          # the fresh-clone run, unedited
└── outputs/
    ├── summary.json
    └── length_vs_mass.png
```

## Rubric (10 points)

| Criterion | Points | What earns full marks |
|---|---|---|
| Numbers correct and reproducible | 2 | Summary matches `seqreport stats --json` on the same file |
| No hard-coded paths | 1 | Input path is an argument; output directory created if missing |
| Exit codes correct | 2 | 0 success, 2 unreadable input; demonstrated, not claimed |
| Determinism proven | 3 | Identical hashes across runs **and** across `PYTHONHASHSEED`, with the commands pasted |
| Tests meaningful | 1 | Four tests, none of which merely call the function to see if it raises |
| README is three commands | 1 | Fresh-clone transcript matches the README exactly |

## Common wrong answers (instructor note)

1. **"The hashes differ but the plot looks the same."** Byte-identical is the
   standard, because the next person will diff files, not eyeball plots. The usual
   causes are Matplotlib metadata, `set` iteration, and unstable sorting of equal
   keys.
2. **Printing progress messages inside `analysis.py`.** A workflow's stdout should
   be either the result or nothing; progress chatter breaks piping and makes the
   transcript unreadable.
3. **Tests that only check "it runs".** A test asserting `main() == 0` on valid input
   proves the function returns something. The summary-number test is what would catch
   a silent change to the analysis.
4. **README that says "install the requirements".** Name the command. A stranger
   cannot install a pronoun.

## Extension

Add a `--min-length` argument and a test that proves it changes the *summary numbers*
in the expected direction. Then add a `Makefile` with `make run` and `make test`, and
explain in one sentence why a Makefile is not the same thing as reproducibility.
