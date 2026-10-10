# Architecture and evidence

The project separates channel definitions, scientific values, execution, and presentation so a visitor can inspect how each result was produced.

## Main components

| Path | Responsibility |
| --- | --- |
| `index.html`, `main.js`, `main.css` | Qollab-injected page fragment, interaction controller, and styles. |
| `channels/api.py` | `ChannelPair` contract, lazy registry, and generic gallery serialization. |
| `channels/*.py` | Channel-pair definitions, strategy metadata, and channel circuits. |
| `quantum/science.py` | Flagship formulas and general analytic helpers. |
| `quantum/engine.py` | Flagship-specific probe circuits, batch execution, result parsing, and benchmarks. |
| `quantum/bridge.py` | Python entry points called by the Qollab JavaScript/Python bridge. |
| `claims.json` | Machine-readable ledger of displayed scientific claims. |
| `tests/` | Formula, circuit, integration, runtime-contract, and accessibility regression checks. |

The page is an HTML fragment because Qollab supplies the surrounding runtime. It expects Qollab to inject the selected backend and expose the Python bridge. Opening `index.html` directly in a browser is not a supported way to run the interactive experience.

## One live job

`get_experience` submits a single `backend.run` call containing four named circuits for the HURTS pair: separable and maximally entangled probes through both channels. The returned counts support one sampled round and both benchmarks. Later UI actions reveal cached evidence. `get_gallery` serializes registered pairs and submits no job.

This one-job contract is specific to the current flagship experience. The pair registry is more general than the execution engine by design; a gallery entry alone does not imply a live Qollab benchmark.

## Evidence labels

- `EMPIRICAL`: an estimate from sampled outcomes, accompanied by the run context.
- `ANALYTIC`: a value derived from a formula for the stated strategy. Where the label is used for an optimum, the corresponding implementation and tests must support that statement.
- `THEORETICAL_CEILING`: a theoretical bound or optimum without a validated live measurement path in this project.

The site must not invent a fallback number after a failed run. The code reports the selected Qollab backend without guessing its hardware class. Local statevector verification is useful evidence for circuit behavior, but it is not hardware data.

## Test layers

The unit tests verify equations, states, circuits, and parsing. Contract tests check that Qollab-facing payloads preserve provenance and JSON compatibility. Static runtime tests inspect the submission surface. The test for the actual Qollab browser runtime remains skipped until that external environment can execute it.
