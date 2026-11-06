# Challenge 01 — The alphabet problem

**Level:** L4 (challenge) · **Weight:** 15% · **Time:** 4–8 hours · **No single right answer**

## The problem

`seqreport` decides whether a sequence is protein or nucleotide with a heuristic
(`guess_molecule_type`) that is wrong in both directions, and it validates against
one fixed alphabet per molecule type. Both decisions are defensible for a teaching
tool and both are wrong for a production one.

Your task: design the alphabet layer you would actually ship, and defend it.

## The specific difficulty

Consider each of these, and decide what your design does:

| Sequence | What is it? | What does a naive validator do? |
|---|---|---|
| `MEEPQSDPSV` | protein | fine |
| `ACGTACGTACGT` (12 nt) | nucleotide | fine |
| `GGGGCCCCTTTT` (12 nt) | nucleotide **or** a glycine/proline-rich peptide | guesses nucleotide |
| `NNNNNNNNNNNNNNNNNNNNNN` | nucleotide with all-ambiguous bases | guesses protein, because `N` is also asparagine |
| `MEEPQSDPSVX` | protein with an unknown residue | fine, if you allow `X` |
| `ACGTACGUACGT` | RNA | fine, if `U` is allowed for nucleotides |
| `ACGTACGTACGTU` mixed | not a real molecule; a join error between two records | silently passes both alphabets |
| `MEEP*` | protein with a stop | fine as protein; `*` is invalid in DNA |
| `MKWVTFISLL` (10 aa) | short protein | `unknown` — too short to guess |

Every one of these is a real case that arrives in real files.

## Task

1. **Write `alphabets.py`** defining:
   - the alphabets you support (DNA, RNA, protein, and any you decide are needed);
   - a validator that, given a sequence and a *declared* alphabet, returns the set
     of offending characters (not a boolean — the characters are the useful part);
   - a *detector* that returns a ranked list of plausible alphabets with a score,
     rather than a single guess. An explicit `unknown` result is allowed and must be
     preferred over a wrong confident answer.
2. **Handle the ambiguous cases explicitly.** For at least four rows of the table,
   write a test that pins your decision, and one sentence saying whether another
   reasonable person could decide differently.
3. **Measure the failure rate.** Construct a corpus of at least 40 sequences (you may
   use the repository data plus your own constructions, clearly labelled) and report
   how often your detector's top answer is correct. Report the confusion matrix.
   **Do not tune on the corpus you report** — split it, or build the corpus after the
   design is frozen, and say which you did.
4. **Write `DESIGN.md`** (max 2 pages) covering: the interface, the ranking rule and
   why it is defensible, what your detector cannot do, and the one case where you
   chose to fail loudly rather than guess.

## Deliverables

```text
challenge-01/
├── alphabets.py
├── test_alphabets.py
├── corpus/sequences.fasta        # 40+ sequences, each labelled with its truth
├── corpus/report.md              # confusion matrix + method
└── DESIGN.md
```

## Rubric (20 points)

| Criterion | Points | What earns full marks |
|---|---|---|
| Validator returns offending characters | 3 | Not a boolean; the error message is usable without rerunning |
| Detector returns ranked answers | 3 | Scores are interpretable; `unknown` is a first-class answer |
| Four ambiguous cases pinned by tests | 4 | Each test names the alternative interpretation and why it lost |
| Corpus and measurement | 5 | 40+ labelled sequences; confusion matrix; no tuning on reported set (or explicitly admitted) |
| Design document | 3 | States the trade-off, not just the choice |
| Reproducibility | 2 | One command regenerates `corpus/report.md` |

## What makes this hard (and why it is a challenge, not an assignment)

There is no correct answer, only defensible ones. A detector with no false positives
will refuse most short sequences. A detector with no refusals will confidently
mislabel them. The mark is for knowing *which* trade-off you made, measuring it, and
saying so — not for a higher accuracy number on a corpus you designed yourself.

## Integrity and attribution

- AI assistance permitted with disclosure.
- If you reuse `guess_molecule_type`'s logic as a baseline, cite the file and compare
  against it — a baseline is good practice, not a weakness.
- No citation of this course is required or rewarded.
