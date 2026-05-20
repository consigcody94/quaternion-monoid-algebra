# arXiv submission package

This folder contains the arXiv-ready manuscript for the quaternion-monoid algebra paper.

- `main.tex` — the manuscript (conservative LaTeX: article class, amsmath/amssymb only, no exotic packages, compiles cleanly under arXiv's TeXLive)
- `main.pdf` — locally compiled reference PDF (tectonic), for your own preview

## Status

**Blocked on endorsement, not on the manuscript.** The paper is submission-ready. arXiv requires a first-time submitter in a given subject area to be endorsed by an established author in that area. As of January 2026 an institutional email no longer qualifies on its own, so the realistic path is a personal endorsement.

## Category choice

arXiv endorsement is **per subject area**, so the category we submit to has to be one the endorser actually has endorsement standing in. The paper fits several:

| Category | Fit | Notes |
|---|---|---|
| `cs.CR` (Cryptography and Security) | Strong | The algebraic chain-verification application; broad category |
| `cs.DM` (Discrete Mathematics) | Strong | The monoid construction itself |
| `math.RA` (Rings and Algebras) | Strong | Pure-algebra framing; math endorsement is the strictest, avoid unless the endorser is a mathematician |
| `eess.SP` (Signal Processing) | Moderate | The quaternion / IMU-data angle |
| `cs.AR` (Hardware Architecture) | Moderate | The single-cycle hardware sketch; good fit if the endorser is a hardware person |

**Recommendation:** ask the endorser which category they can endorse in, then pick the best-fitting one from their options. For a hardware/AI endorser, `cs.AR` or `eess.SP` is most likely within their standing; for a CS-theory endorser, `cs.CR` or `cs.DM`.

## How to submit (once endorsed)

1. Create an account at https://arxiv.org with your ORCID (free; get an ORCID at https://orcid.org if you don't have one).
2. Request endorsement for the chosen category. arXiv shows an endorsement code on your submission page; send that code to your endorser, or have them go to https://arxiv.org/auth/endorse and enter it.
3. Once endorsed, start a new submission, upload `main.tex` (and `main.pdf` is generated server-side; you can also upload it as the reference).
4. Set the primary category and any cross-lists (e.g., primary `cs.CR`, cross-list `cs.DM`).
5. Add the license (arXiv offers CC BY 4.0, CC BY-SA, or the arXiv non-exclusive license; CC BY 4.0 matches the spirit of the MIT code release).
6. Review arXiv's auto-compiled PDF preview, then submit. Moderation typically clears in 1–3 business days.

## Reproducing the PDF locally

```bash
# tectonic (single binary, fetches packages on first run)
tectonic main.tex

# or with a full TeXLive install
pdflatex main.tex && pdflatex main.tex
```
