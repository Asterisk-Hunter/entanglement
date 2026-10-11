# Entanglement Trap

**Does maximum entanglement always help?** Choose a probe, try to identify an unknown quantum channel, and compare both strategies using results from one Qiskit backend job.

[Watch the 2:30 demo](https://drive.google.com/file/d/1AtWwNPAnjLCQPXdTPFlGnzqjLQ9pgD2w/view?usp=sharing) · [Open the Qollab project](https://qollab.xyz/p/01a1299b-dba2-772e-a6e7-8012098938f0)

[Read the field guide](https://github.com/Asterisk-Hunter/entanglement/blob/main/docs/src/SUMMARY.md) · [Explore the source](https://github.com/Asterisk-Hunter/entanglement)

## What is it?

Entanglement Trap is an interactive quantum channel-discrimination laboratory. Its learning path is **choose → run → compare → explain → inspect**.

- **Experiment:** a live Identity-vs-`V` channel-discrimination run with both probe strategies, one sampled round, and empirical results.
- **Proof:** four interactive figures showing output distinguishability, the dimension sweep, eigenvalue geometry, and the relation to entanglement entropy.
- **Resource Lab:** a channel-pair gallery comparing cases where maximum entanglement hurts, helps, or ties. This gallery reads analytic metadata and submits no backend jobs.
- **Evidence:** source labels, confidence intervals, exact values, and a `claims.json` ledger connecting the displayed quantities to their formulas and references.

**Resource Lab is the gallery within this project.** The separate **Entangle Lab** singlet/CHSH companion in the full repository is a local browser app; it is not included in the published Qollab project.

## Why does it matter, and who is it for?

Entanglement is a resource, not a universal upgrade. This experiment helps learners and quantum developers evaluate the complete **probe–channel–measurement strategy**, rather than assume maximum entanglement gives maximum performance.

It is for **students** building quantum intuition, **educators** demonstrating a counterexample, and **technical reviewers or developers** inspecting the circuits, formulas, and evidence. The game provides an accessible entry point; the figures and seven-chapter field guide support deeper study.

Its practical value is educational: making resource choices and measurement assumptions visible. It does not claim a deployed engineering application or computational advantage.

## How does the quantum part work?

In channel discrimination, a referee chooses one of two transformations with equal probability. You prepare a probe, use the unknown transformation once, then measure the output to identify it. An entangled probe includes a reference register that stays outside the channel.

Live results use the dimension and shot count selected for that run. The proof section and gallery also show analytic reference values, including the flagship result at **dimension 256**. Those reference values are separate from the live measurements.

| Channel pair | Separable | Max entanglement | Evidence |
| --- | ---: | ---: | --- |
| Identity vs. `V`, dimension 256 | 100% | 50.78% | Analytic success probabilities for the implemented strategies; both have live circuit paths. |
| Identity vs. fully depolarizing qubit channel | 75% | 87.5% | Analytic separable value and a theoretical entangled ceiling. The live measurement attaining the ceiling is not implemented. |
| Four-Pauli rotations, θ = π/8 | 85.36% | 85.36% | Analytic optima; the Bell discriminator is also checked using exact statevector simulation. |

For Identity vs. `V` at dimension 256, the implemented maximally entangled measurement gives `0.507781982421875`. Its optimal Helstrom ceiling is `0.5623778102448098`. The app distinguishes the implemented strategy from the theoretical ceiling.

The takeaway is specific: **maximum entanglement does not guarantee maximum performance.** The result depends on the channel pair, probe, and measurement.

### Why the flagship result happens

The flagship compares the identity transformation with a reflection:

```text
V = 2 |0…0⟩⟨0…0| − I
```

For the maximally entangled input, the two possible pure outputs have signed overlap `(2 − d) / d`. Its magnitude approaches one as dimension grows: the outputs become harder to tell apart even though the input remains maximally entangled.

```text
Output overlap:                 c(d) = (2 − d) / d
Implemented measurement:        p_simple(d) = 1 − c(d)² / 2
Optimal measurement for probe:  p_Helstrom(d) = (1 + √(1 − c(d)²)) / 2
```

The separable strategy prepares a state whose two outputs are orthogonal, allowing perfect discrimination in the ideal model. Its success is not limited by the nearly identical outputs produced by the maximally entangled input.

At dimension 16, the implemented entangled strategy's analytic success is **61.72%**, compared with **100%** for the separable strategy. This contrast makes a useful first live demonstration. The dimension sweep shows the trend toward chance; the eigenvalue and entropy figures explain the probe dependence geometrically.

### Evidence you can audit

| Label | Meaning | How to interpret it |
| --- | --- | --- |
| **EMPIRICAL** | Correct guesses divided by trials in the selected backend run. | Read with the dimension, shot count, backend, and 95% confidence interval. |
| **ANALYTIC** | A formula-derived probability for the stated strategy. | A reference prediction, not an observation from the current run. |
| **THEORETICAL CEILING** | An optimal probability or bound distinct from the implemented measurement. | An attainable theoretical target or bound; not an executed result. |

With 100 shots per channel, each probe's benchmark pools 200 trials across the two channels. Finite-shot rates fluctuate. The code uses Agresti–Coull confidence intervals, which remain informative even when every observed trial succeeds. A failed run produces an error message rather than invented evidence.

### Implementation

Qollab loads the HTML fragment, `main.js`, and `main.css`, and supplies the selected backend. `quantum/bridge.py` returns the shared run payload; `quantum/engine.py` compiles and executes the four-circuit batch. `quantum/science.py` provides formulas, `channels/` defines the pairs, and `ui/` renders the explanations.

The live runner is specific to Identity vs. `V`. The gallery registry supports all three pairs' metadata. The architecture chapter below explains this boundary and the one-job design.

### Scientific scope and credit

The underlying channel-discrimination results are prior work. Entanglement Trap contributes the interactive experiment, shared-batch execution, visual explanations, and traceable evidence labels.

- The flagship counterexample is credited to **Lien and Quintino (2026, preprint)**.
- The one-query discrimination bound is credited to **D'Ariano, Lo Presti and Paris, J. Opt. B 4, S273 (2002)**.
- The unitary-channel comparison draws on **Manna, Das Bhowmik and Saha, Phys. Rev. A 112, 042215 (2025)**.

Small instances are classically simulable; no computational advantage is claimed. Analytic predictions and theoretical ceilings are labeled separately from measured backend results. Backend selection comes from Qollab; a simulator run is not presented as hardware evidence. See `claims.json` and `attribution.md` in the project source for provenance and build credit.

## How do I run it?

1. Choose an available simulator on Qollab and start a project **Run**.
2. Wait for **READY**, then choose **Separable** or **Max entanglement**. Start with dimension **16** and **100 shots per channel**.
3. Click **Play one round**. The app submits four circuits in one backend call, gathering results for both strategies.
4. Compare the empirical win rates and confidence intervals. Open **Strategy details**, explore **The proof**, and inspect the channel pairs in **Resource Lab**.

The displayed round is sampled from the measured batch. A single win or loss does not establish a success rate. Comparisons reuse the same results and submit no further jobs. To run another experiment—or retry after a failure—start a new Qollab **Run**.

### Local development

These instructions use the **full repository checkout**. Local preview files, development tests, documentation, and the companion app are not part of the published Qollab file bundle.

For an analytic UI preview:

```sh
python -m http.server 8000
```

Open `http://localhost:8000/preview.html`. Live execution is disabled in this preview because it requires Qollab's injected backend. The optional companion is at `http://localhost:8000/entangle-lab/`; it evaluates ideal singlet probabilities in JavaScript and uses no quantum backend.

For local checks, use Python 3.12.14 and the pinned development dependencies:

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

On Windows, create the environment with `py -3.12 -m venv .venv` and activate it with `.venv\Scripts\Activate.ps1`.

The local suite covers analytic formulas, circuits, result parsing, registry contracts, and the Python bridge. Its hosted-browser integration case is skipped locally because it requires Qollab's runtime.

To read the book locally, run `mdbook serve --open` from `docs/`. Maintained sources live in `docs/src/`; generated pages go to `docs/book/`. The companion has its own guide under `entangle-lab/docs/`.

### Field guide: from intuition to implementation

The seven-chapter mdBook develops the explanation from first principles through reproducible implementation. These public Markdown links work outside Qollab:

| Chapter | What it helps you do |
| --- | --- |
| [Introduction](https://github.com/Asterisk-Hunter/entanglement/blob/main/docs/src/index.md) | Understand the question, audience, and scientific scope. |
| [Run the lab](https://github.com/Asterisk-Hunter/entanglement/blob/main/docs/src/run-the-lab.md) | Run the Qollab experiment and reproduce local checks. |
| [Channel discrimination](https://github.com/Asterisk-Hunter/entanglement/blob/main/docs/src/channel-discrimination.md) | Learn the decision task, trace-norm bound, and flagship formulas. |
| [Three channel-pair results](https://github.com/Asterisk-Hunter/entanglement/blob/main/docs/src/results.md) | Compare the pairs with their strategy and evidence qualifications. |
| [Add a channel pair](https://github.com/Asterisk-Hunter/entanglement/blob/main/docs/src/add-a-pair.md) | Implement the shared interface and document new claims. |
| [Architecture and evidence](https://github.com/Asterisk-Hunter/entanglement/blob/main/docs/src/architecture.md) | Trace the one-job design, module responsibilities, and validation layers. |
| [Limits and sources](https://github.com/Asterisk-Hunter/entanglement/blob/main/docs/src/limits-and-sources.md) | Check the research references, limitations, and historical-value audit. |

### Extend the laboratory

Use `channels/four_pauli.py` as a worked example. Implement `build_a`, `build_b`, `strategies`, and `analytic_bounds`; register the pair in `channels/api.py` and document its claims in `claims.json`. Verify formulas, circuits, labels, and payloads. Gallery registration alone does not create a live benchmark: a new live pair also needs validated preparation, measurement, result parsing, and bridge/UI integration. The extension chapter walks through these steps.

## Acknowledgment and license

This effort is supported by Qollab & IonQ.

MIT. See `LICENSE` in the project source.
