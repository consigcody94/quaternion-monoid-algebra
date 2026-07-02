# JOSS submission readiness

Tracking readiness for a submission to the [Journal of Open Source Software](https://joss.theoj.org). JOSS is free, peer-reviewed (openly, on GitHub), and a good fit for this kind of research software. This file tracks what is done and what gates the submission.

## The gating constraint: development history

JOSS requires software that demonstrates **iterative public development over time**, not a single concentrated burst. Their reviewers look for a minimum of roughly **six months of public commit history** with genuine ongoing work. A repository created in one session and left dormant will be declined at editor pre-screen regardless of code quality.

**This is the real gate.** It is not satisfied by waiting six months; it is satisfied by *developing in the open over* six-plus months. The "Open questions" section of the paper is the development roadmap that produces that history.

**Earliest realistic submission window:** ~November 2026, assuming continued development between now and then.

## Criteria checklist

| JOSS criterion | Status |
|---|---|
| OSI-approved open-source license | DONE (MIT) |
| Public repository, browsable without registration | DONE |
| `paper.md` in JOSS format | DONE (`paper/paper.md`) |
| `paper.bib` with references | DONE (`paper/paper.bib`) |
| Automated tests | DONE (pytest + Hypothesis suite, plus `tests/run_all.py` + `tests/stress_tests.py`) |
| Continuous integration | DONE (`.github/workflows/ci.yml`: lint + test matrix) |
| Installable package (`pip install`) | DONE (v0.2.0: `pyproject.toml`, `quaternion_monoid_algebra` package) |
| Documentation: installation | DONE (README) |
| Documentation: example usage | DONE (README quick-start + `examples/`) |
| Documentation: API / functionality | DONE (README + paper) |
| Community guidelines (`CONTRIBUTING.md`) | DONE |
| Statement of need | DONE (in `paper/paper.md`) |
| Tagged release with archive + DOI | DONE (v0.1.0, Zenodo 10.5281/zenodo.20301069) |
| Substantial scholarly effort | PARTIAL — needs the development-history dimension above |
| ~6 months iterative public development | NOT YET — the gate; build it between now and ~Nov 2026 |

## What to do between now and submission

To convert this from "staged" to "submittable," accumulate genuine development history by working the roadmap in the paper's "Open questions" section:

- ~~Package the library for installation and add a property-based (Hypothesis) test suite~~ — done in v0.2.0 (2026-07-01), along with the vectorized batch API and input validation
- Add a formal proof (or partial characterization) of the topology-preservation property
- Add alternative sub-field constructions and document the trade-offs
- Add real-world dataset validation beyond TUM (EuRoC MAV, JIGSAWS, IMU recordings)
- Add a hardware reference (Verilog/SystemVerilog) and synthesis numbers
- Respond to any issues or PRs that come in
- Cut additional tagged releases (v0.2.0, etc.) as the work grows

## Submission process (when ready)

1. Confirm the repository meets all criteria above, including development history.
2. Fill the submission form at https://joss.theoj.org/papers/new.
3. A managing editor opens a pre-review issue in the JOSS reviews repository.
4. Two or more reviewers are assigned; review happens openly on GitHub.
5. Respond to reviewer feedback (typically within 2 weeks per round, 4–6 weeks total).
6. On acceptance, cut a final tagged release and confirm the Zenodo archive.

No submission fees.
