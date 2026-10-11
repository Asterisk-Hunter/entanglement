# Entanglement Trap

**Does maximum entanglement always help?** Choose a probe, try to identify an unknown quantum channel, and compare both strategies using results from one Qiskit backend job.

[Watch the 2:30 demo](https://drive.google.com/file/d/1AtWwNPAnjLCQPXdTPFlGnzqjLQ9pgD2w/view?usp=sharing) · [Open the Qollab project](https://qollab.xyz/p/01a1299b-dba2-772e-a6e7-8012098938f0)

[Read the field guide](https://github.com/Asterisk-Hunter/entanglement/blob/main/docs/src/SUMMARY.md) · [Explore the source](https://github.com/Asterisk-Hunter/entanglement)

## The question behind the experiment

In channel discrimination, a referee chooses one of two transformations with equal probability. You prepare a quantum state, use the unknown transformation once, then measure the output to decide which transformation was applied.

A separable probe uses the system alone. An entangled probe shares a state with a reference register that stays outside the channel. That extra reference can help distinguish outputs—but the amount of entanglement alone does not determine success. The channel pair and the measurement matter too.

Entanglement Trap turns that distinction into a learning sequence: **choose → run → compare → explain → inspect**. The flagship counterexample is supported by two contrasting examples, so visitors can investigate when the resource helps rather than leave with a blanket claim about entanglement.

## Choose your learning path

| Visitor | Start with | Go deeper |
| --- | --- | --- |
| **New to quantum computing** | Play one round and compare the two probes. | Read the channel-discrimination introduction; explore why similar outputs are harder to distinguish. |
| **Student or educator** | Use the live comparison and dimension sweep. | Connect output overlap, measurement, and success probability through the field guide. |
| **Technical reviewer** | Inspect the empirical labels, confidence intervals, and exact values. | Trace the channel circuits, analytic formulas, and claim records in the source. |
| **Contributor** | Inspect the Resource Lab registry and worked channel-pair examples. | Add a pair, document its evidence, and implement a live measurement path when appropriate. |

## Try it

1. Choose an available simulator on Qollab and start a project **Run**.
2. Wait for **READY**, then choose **Separable** or **Max entanglement**. Start with dimension **16** and **100 shots per channel**.
3. Click **Play one round**. The app submits four circuits in one backend call, gathering results for both strategies.
4. Compare the empirical win rates and confidence intervals. Open **Strategy details**, explore **The proof**, and inspect the channel pairs in **Resource Lab**.

The displayed round is sampled from the measured batch. A single win or loss does not establish a success rate. Comparisons reuse the same results and submit no further jobs. To run another experiment—or retry after a failure—start a new Qollab **Run**.

## What is on the Qollab page

- **Experiment:** a live Identity-vs-`V` channel-discrimination run with both probe strategies, one sampled round, and empirical results.
- **Proof:** four interactive figures showing output distinguishability, the dimension sweep, eigenvalue geometry, and the relation to entanglement entropy.
- **Resource Lab:** a channel-pair gallery comparing cases where maximum entanglement hurts, helps, or ties. This gallery reads analytic metadata and submits no backend jobs.
- **Evidence:** source labels, confidence intervals, exact values, and a `claims.json` ledger connecting the displayed quantities to their formulas and references.

**Resource Lab is the gallery within this project.** The separate **Entangle Lab** singlet/CHSH companion in the full repository is a local browser app; it is not included in the published Qollab project.

### Two experiences in the full repository

| | Entanglement Trap | Entangle Lab companion |
| --- | --- | --- |
| **Question** | How does the probe affect channel discrimination? | How do measurement angles affect entangled-pair correlations? |
| **Experience** | A channel-identification game, repeated trials, proof figures, and a comparison gallery. | Adjustable Alice/Bob analyzers, single-pair sampling, and finite-shot CHSH estimates. |
| **Model** | Qiskit circuits through the Qollab-selected backend, plus labeled analytic references. | Ideal singlet probabilities calculated in JavaScript; no quantum backend. |
| **Documentation** | Seven field-guide chapters covering the task, results, execution, architecture, extensions, and limits. | An introduction and eight chapters covering qubits, singlets, measurement, CHSH, implementation, and limits. |
| **Availability** | The published Qollab submission. | The full repository under `entangle-lab/`; run locally using the instructions below. |

The companion builds intuition about correlations. The submitted experiment examines distinguishability. They support the same learning journey while answering different questions.

## Read the results correctly

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

| Dimension | Separable strategy | Implemented entangled strategy |
| ---: | ---: | ---: |
| 4 | 100% | 87.50% |
| 16 | 100% | 61.72% |
| 64 | 100% | 53.08% |
| 256 | 100% | 50.78% |

These are analytic reference values, not backend measurements. Dimension 16 is a useful starting point for a live demonstration because its predicted contrast is visible without trying to resolve a tiny deviation from chance.

### What each figure explains

| Figure | What to look for | What it establishes |
| --- | --- | --- |
| **Output-state distinguishability** | Increasing similarity of the two maximally entangled outputs. | A resource can remain maximal while information useful for this decision decreases. |
| **Dimension sweep** | The entangled strategy approaching 50%, while the separable strategy stays at 100%. | The trend across dimensions, with the implemented strategy separate from the optimal ceiling. |
| **Eigenvalue geometry** | The reachable set and its nearest point to zero; drag an eigenvalue to explore. | A geometric explanation of how probe choice changes the output overlap. |
| **Entropy / Helstrom map** | Success bounds across the displayed family of probe states. | Entanglement entropy alone does not specify discrimination performance. |

### Evidence you can audit

| Label | Meaning | How to interpret it |
| --- | --- | --- |
| **EMPIRICAL** | Correct guesses divided by trials in the selected backend run. | Read with the dimension, shot count, backend, and 95% confidence interval. |
| **ANALYTIC** | A formula-derived probability for the stated strategy. | A reference prediction, not an observation from the current run. |
| **THEORETICAL CEILING** | An optimal probability or bound distinct from the implemented measurement. | An attainable theoretical target or bound; not an executed result. |

With 100 shots per channel, each probe's benchmark pools 200 trials across the two channels. Finite-shot rates fluctuate. The code uses Agresti–Coull confidence intervals, which remain informative even when every observed trial succeeds. A failed run produces an error message rather than invented evidence.

## Scientific scope and credit

The underlying channel-discrimination results are prior work. Entanglement Trap contributes the interactive experiment, shared-batch execution, visual explanations, and traceable evidence labels.

- The flagship counterexample is credited to **Lien and Quintino (2026, preprint)**.
- The one-query discrimination bound is credited to **D'Ariano, Lo Presti and Paris, J. Opt. B 4, S273 (2002)**.
- The generalized channel-discrimination formulas are credited to **Manna, Das Bhowmik and Saha, Phys. Rev. A 112, 042215 (2025)**.

Small instances are classically simulable; no computational advantage is claimed. Analytic predictions and theoretical ceilings are labeled separately from measured backend results. Backend selection comes from Qollab; a simulator run is not presented as hardware evidence. See `claims.json` and `attribution.md` in the project source for provenance and build credit.

## Implementation

The root `index.html` is a Qollab-injected HTML fragment. Qollab loads `main.js` and `main.css`, supplies the selected backend, and exposes the Python bridge.

| Source | Role |
| --- | --- |
| `quantum/bridge.py` | Shared run payload, sampled round, benchmarks, and gallery metadata. |
| `quantum/engine.py` | Four-circuit batch, portable gate compilation, execution, and count parsing. |
| `quantum/science.py` | Analytic reference formulas. |
| `channels/` | Channel definitions, strategy metadata, and registry. |
| `ui/` | Interactive figures, results, and gallery. |

### One batch, a complete comparison

```text
Choose a probe and run settings
            ↓
get_experience → build and compile four circuits
            ↓
one backend.run: sep_I · sep_V · me_I · me_V
            ↓
measured counts → sampled round + both benchmarks
            ↓
cached comparisons, explanations, and strategy details
```

The selected probe controls which counts supply the displayed round. Both probe benchmarks are calculated from the shared batch, so switching the comparison does not consume another backend job. Circuit compilation uses a portable `rx`, `ry`, `rz`, `cx` basis before execution. Gallery discovery stays separate and submits no job.

The registry is broader than the current live engine: all three pairs have inspectable metadata, while the shared live runner is specific to Identity vs. `V`. This boundary is explicit in the bridge, UI labels, and documentation.

## Field guide: from intuition to implementation

The `docs/` folder contains a maintained mdBook with a dark theme matching the experiment and mathematical notation support. Its chapters are also available as Markdown in the public repository, so the documentation links below work outside the Qollab runtime.

| Chapter | What it helps you do |
| --- | --- |
| [Introduction](https://github.com/Asterisk-Hunter/entanglement/blob/main/docs/src/index.md) | Understand the question, audience, and scientific scope. |
| [Run the lab](https://github.com/Asterisk-Hunter/entanglement/blob/main/docs/src/run-the-lab.md) | Run the Qollab experiment and reproduce local checks. |
| [Channel discrimination](https://github.com/Asterisk-Hunter/entanglement/blob/main/docs/src/channel-discrimination.md) | Learn the decision task, trace-norm bound, and flagship formulas. |
| [Three channel-pair results](https://github.com/Asterisk-Hunter/entanglement/blob/main/docs/src/results.md) | Compare the pairs with their strategy and evidence qualifications. |
| [Add a channel pair](https://github.com/Asterisk-Hunter/entanglement/blob/main/docs/src/add-a-pair.md) | Implement the shared interface and document new claims. |
| [Architecture and evidence](https://github.com/Asterisk-Hunter/entanglement/blob/main/docs/src/architecture.md) | Trace the one-job design, module responsibilities, and validation layers. |
| [Limits and sources](https://github.com/Asterisk-Hunter/entanglement/blob/main/docs/src/limits-and-sources.md) | Check the research references, limitations, and historical-value audit. |

The current Qollab bundle contains the runnable app and claim ledger, not the mdBook source or companion app. The public repository supplies those additional resources.

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

The local suite covers analytic formulas, circuits, result parsing, registry contracts, and the Python bridge. Its hosted-browser integration case is skipped locally because it requires Qollab's runtime. The field guide is in `docs/src/`; build it with `mdbook build` from `docs/`.

To inspect the registered analytic values without submitting a backend job:

```sh
python -c "from channels.api import available_pairs, load_pair; [print(load_pair(s).name, load_pair(s).analytic_bounds()) for s in available_pairs()]"
```

To build and read the field guide locally:

```sh
cd docs
mdbook build
mdbook serve --open
```

Generated pages go to `docs/book/` and are ignored by Git. The maintained sources are in `docs/src/`, navigation is in `SUMMARY.md`, and book settings are in `book.toml`. The companion has its own guide under `entangle-lab/docs/`.

### Extend the laboratory

1. Use `channels/four_pauli.py` as a worked example. Define a unique slug, name, citation, reference dimension, channel circuits, and strategy records.
2. Register the pair in `channels/api.py`. Add formula, value, dimension, source, and evidence records to `claims.json`; connect their IDs to the displayed strategies.
3. Check the formulas, circuits, serialization, and labels. If claiming an implemented measurement attains an optimum, include an independent matrix or statevector comparison.
4. For live execution, implement and validate the probe preparation, measurement, result parsing, and bridge/UI path. Keep a metadata-only entry labeled accordingly until that work exists.

New pairs implement `build_a`, `build_b`, `strategies`, and `analytic_bounds`, then register in `channels/api.py`. Gallery metadata alone does not create a live benchmark: each new pair needs a verified probe, measurement, and execution path.

## Acknowledgment and license

This effort is supported by Qollab & IonQ.

MIT. See `LICENSE` in the project source.
