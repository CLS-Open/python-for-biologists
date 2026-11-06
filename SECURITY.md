# Security policy

## What this repository actually is

`seqreport` is a small teaching package: a FASTA parser, composition statistics, a fixed
set of quality checks and three report renderers. It reads local files and prints text.
It has **no network access, no shell execution, no subprocess calls, no plugin loader and
no evaluation of user input**. `scripts/fetch_datasets.py` is the only code that touches
the network, and it is a maintenance script that talks to the UniProt REST API — it is not
imported by the package and is never run by learners.

That leaves three realistic concerns, all worth reporting:

1. **Parser memory exhaustion.** Input is untrusted data, not a sandbox. A file with a
   single header millions of characters long, or a truncated gzip stream, can still
   consume more memory than the file size suggests. `seqreport.records` validates record
   shape and characters; it does not bound memory. Do not point it at files you would not
   open in a text editor.
2. **Wrong results presented as right ones.** For teaching software this is the
   security-relevant failure mode: if the checker misses a defect, or the molecular weight
   is wrong, a learner learns the wrong thing and a downstream analysis inherits the
   error. Report any case where `seqreport` disagrees with Biopython or with a
   hand-computed expectation.
3. **Report injection.** Record identifiers and descriptions come from the input file and
   are embedded in HTML reports. They are escaped (`html.escape`) and a test asserts that
   an identifier containing `<script>` does not become markup. If you find an escaping
   hole, that is a genuine security bug: a report is meant to be safe to send to a
   collaborator who will open it.
4. **Supply chain.** Runtime dependencies: none beyond the standard library. Development
   and CI dependencies are declared in `pyproject.toml`; Dependabot alerts are enabled.
   Report any unexpected dependency change or any release artefact that does not match the
   committed source.

## Not in scope

- Vulnerabilities in Python itself, Biopython, Matplotlib, pytest or MkDocs. Report those
  upstream.
- Anything requiring the attacker to already have write access to the repository.
- The security posture of `uniprot.org`. We link to it; we do not operate it.

## Reporting

**Contact:** *the maintainer must insert a working address before public launch — no
contact address is invented here.*

Once an address exists: reports are acknowledged within 7 days, and a fix or a written
decision not to fix is given within 30 days. Credit is given in the release notes unless
you ask otherwise. There is no bug bounty, and there will not be one: this is an unfunded
educational project.
