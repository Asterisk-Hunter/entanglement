# Attribution and build history

## Original contribution

Entanglement Trap implements an interactive channel-discrimination experiment, a shared four-circuit Qiskit batch, analytic explanations, a channel-pair registry, evidence labels, and a claim ledger. The underlying scientific results are credited below; no discovery of those results or quantum computational advantage is claimed.

The full repository also contains the Entangle Lab singlet/CHSH companion and its guide. That companion runs locally and is separate from the published Qollab experiment and its Resource Lab gallery.

## Recorded development

The repository's commit history begins on **October 10, 2026 at 11:16 IST**. It records implementation and submission work during the October 9–11 Qollab hackathon. The table identifies recorded phases; subsequent documentation cleanup is visible in the working tree until committed.

| Phase | Commits | Recorded time (IST) |
| --- | --- | --- |
| Science kernel, claim ledger, channels, engine, UI, and regression checks | `c35e7e8` → `5547e24` | Oct 10, 11:16–11:17 |
| Entangle Lab app and field guide | `2d31ac0` → `b219642` | Oct 10, 21:16–21:25 |
| Repository restructure and submission scoping | `246c952` → `fd8372b` | Oct 10, 22:35–22:38 |
| Trap documentation and earlier launch-video work | `131dbf4` → `bfc2c70` | Oct 11, 01:06–10:34 |
| Qollab runtime compatibility, UI refinement, local preview, and dependency cleanup | `24148e5` | Oct 11, 12:42 |
| Submission demonstration recording and export | `6c52928` | Oct 11, 14:19 |
| Submission README | `43fdd90` | Oct 11, 14:28 |

Inspect the complete record with:

```sh
git log --reverse --format="%h | %aI | %s"
```

## Scientific sources

| Source | Use in this project |
| --- | --- |
| Kristin Sundal Lien and Marco Túlio Quintino, [“Entanglement in quantum channel discrimination: sometimes less is more,” arXiv:2605.31519 (2026)](https://arxiv.org/abs/2605.31519) | Source of the flagship counterexample. |
| G. M. D'Ariano, P. Lo Presti, and M. G. A. Paris, [“Improved discrimination of unitaries by entangled probes,” J. Opt. B 4, S273–S276 (2002)](https://arxiv.org/abs/quant-ph/0204050) | Unitary-discrimination theory and geometric context. |
| Satyaki Manna, Anandamay Das Bhowmik, and Debashis Saha, [“Limitation of maximally entangled probes for single-shot distinguishability of unitaries,” Phys. Rev. A 112, 042215 (2025)](https://doi.org/10.1103/bsxv-q9x7) | Context for the unitary-channel comparison, not the depolarizing-channel derivation. |
| Clauser, Horne, Shimony, and Holt, [Phys. Rev. Lett. 23, 880 (1969)](https://doi.org/10.1103/PhysRevLett.23.880) | CHSH inequality explained in the companion guide. |

`claims.json` records each displayed scientific quantity with its formula, dimension, source, and evidence kind. The historical printed value `0.5078125` is retained for audit and marked unsafe for display; the implemented formula gives `0.507781982421875`.

## Dependencies and services

These components are used by the project and retain their upstream licenses:

| Component | Use and distribution |
| --- | --- |
| Qiskit | Circuit construction and portable compilation; supplied by Qollab for hosted execution. |
| Qiskit Aer | Local development and circuit verification; pinned in `requirements-dev.txt`. |
| NumPy and SciPy | Scientific calculations; declared in the dependency manifests. |
| pytest | Local regression and contract checks; development dependency. |
| mdBook | Field-guide generation; the book configuration enables MathJax support. |
| Manrope and DM Mono | Companion typography, requested from Google Fonts; font files are not vendored. |
| Qollab and IonQ | Hosting and the externally selected quantum backend. |

The main Qollab interface uses system fonts and has no vendored frontend library. The MIT license in `LICENSE` covers the project's original source and documentation; it does not replace third-party licenses.

## Demo and production assets

The [2:30 submission demo](https://drive.google.com/file/d/1AtWwNPAnjLCQPXdTPFlGnzqjLQ9pgD2w/view?usp=sharing) uses the team's own screen recording and narration. It preserves the real measured results. Editing shortened pauses, adjusted playback with pitch preserved, normalized audio, cropped recorder controls, and added captions.

Production tools included **FFmpeg**, **Whisper** for transcription, and **HyperFrames 0.8.146** for composition and export. **GSAP 3.14.2** and the installed **Arial** font were used in the production composition; their source/font files are not included in this repository. Only the rendered demo is retained under `videos/submission-demo/`.

Earlier launch-video compositions and their font assets were removed from the current tree. Historical commits retain that production history. Video files and local production tools are separate from the runnable Qollab source bundle.

## Acknowledgment

This effort is supported by Qollab & IonQ.
