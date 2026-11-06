# Challenge 02 — Fail loudly without becoming unusable

**Level:** L4 (challenge) · **Weight:** 15% · **Time:** 4–6 hours

## The problem

Two failure modes are both wrong, and most tools pick one:

- **Permissive tools** repair, skip, or coerce, and report success. The user gets a
  number that is quietly based on data that was thrown away.
- **Strict tools** abort on the first imperfection. The user gets no result at all
  from a file with one bad record in ten thousand.

Real work needs a third thing: process everything, report every defect, refuse to
produce a *result* that depends on a defect — and never lie about which is which.

## Task

Take `seqreport` (or your own Assignment 3 tool) and redesign its failure policy.
Concretely:

1. **Classify defects by their consequence, not their severity word.** Fill this
   table for *your* tool and justify each row:

   | Defect | Can a defensible result still be produced? | What must the output say? |
   |---|---|---|
   | one record with an invalid character | | |
   | duplicated identifier | | |
   | empty sequence | | |
   | internal stop in a protein | | |
   | 40% `X` residues in one record | | |
   | file contains zero records | | |

2. **Implement `run(path, policy)`** where `policy` is one of `strict`, `report`,
   `repair`, with clearly different and documented behaviour:
   - `strict`: first defect stops the run, exit code 2;
   - `report`: process everything, mark affected records, exit 1 if any defect
     invalidates a record;
   - `repair`: as `report`, but also emit a `repairs.json` listing every change made
     to the data, with record id, position, before, after, and reason.
3. **Make `repair` auditable.** A repair that cannot be written to `repairs.json` must
   not happen. This is the whole discipline: silent repair is unacceptable, audited
   repair is fine.
4. **Test the policies against each other.** For each of the six defects above, show
   what each of the three policies does. Produce a table of results, executed, not
   typed.
5. **Write a one-page `POLICY.md`** stating the default policy and why, with the
   argument that would change your mind.

## Deliverables

```text
challenge-02/
├── failure_policy.py         # run(path, policy)
├── test_failure_policy.py
├── policies.md               # the executed table: defect × policy → outcome
├── repairs.json              # example output from the repair policy
├── POLICY.md
└── transcript.txt
```

## Rubric (20 points)

| Criterion | Points | What earns full marks |
|---|---|---|
| Defect classification by consequence | 4 | Justified per row in terms of what result survives |
| Three policies implemented, genuinely different | 4 | Not three names for the same code path |
| Repairs are complete and auditable | 4 | Every mutation appears in `repairs.json` with reason and position |
| Test matrix | 4 | Six defects × three policies, all executed, all asserted |
| POLICY.md argument | 2 | Names the default, the reason, and the evidence that would reverse it |
| No silent data loss anywhere | 2 | Grep-level proof: no `except: pass`, no `.dropna()`-equivalent without a log entry |

## The hard part

`repair` is where people cheat. A repair that changes a `1` to `X` (the "closest"
valid residue) is *not* a repair — it is an invention, and it will be indistinguishable
from real data downstream. Decide whether your tool is allowed to invent values, and
if it is, make `repairs.json` say so in words a reviewer will not misread. (Our answer,
in `seqreport`: **never invent**. Skip, mark, report — but do not fill in.)

## Integrity and attribution

- AI assistance permitted with disclosure.
- Comparing against `seqreport`'s current behaviour is expected; cite where you differ
  and why. Disagreement with the course material is a legitimate result — say so in
  `POLICY.md` if your design is better and show the case that proves it.
- No citation requirement; no marks for citing.
