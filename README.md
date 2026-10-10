# Entanglement Trap

**Entanglement is a resource, not a guarantee.** Entanglement Trap is an interactive, Qiskit-based channel-discrimination lab that compares three carefully labeled cases: entanglement hurts, helps, or ties. Each result is linked to its formula, implementation status, and evidence.

The project is designed for three people:

- **Students** meeting quantum channel discrimination for the first time: compare the probes and see what changes.
- **Educators** who need a short lecture demonstration: use the HURTS result as a 15-second surprise, then unpack the channels and measurement in a three-minute discussion.
- **Researchers** checking assumptions about probe resources: inspect the channel definitions, analytic values, executable circuits, and claim ledger.

The interactive lab runs as a Qollab project. The source page is a Qollab-injected HTML fragment; `main.js` and `main.css` are loaded by the Qollab runtime. The Python bridge uses Qiskit circuits and one backend job for the flagship run. The resource gallery is metadata-only and submits no jobs.

## Three outcomes, one question

For each channel pair, how well can we distinguish the channels with a separable probe and with a maximally entangled probe?

| Case | Channel pair | Separable | Maximally entangled | Evidence |
| --- | --- | ---: | ---: | --- |
| **HURTS** | Identity vs. `V`, `d = 256` | `1.0` | `0.507781982421875` | Both are analytic values for the implemented flagship strategies. The second is executable; neither figure is a hardware measurement. |
| **HELPS** | Identity vs. fully depolarizing qubit channel | `0.75` | `0.875` | The entangled value is a theoretical Helstrom ceiling; its attaining live measurement path is not implemented. |
| **NEUTRAL** | Four-Pauli rotations, `θ = π/8` | `0.8535533905932737` | `0.8535533905932737` | Both optima are analytic; the Bell discriminator is also verified by exact statevector simulation. |

The point is not that entanglement is harmful. Its effect depends on the channel pair and on the discrimination strategy. The gallery makes those comparisons inspectable instead of presenting one surprising number without context.

## Add an experiment

The channel-pair interface is deliberately small. A minimal pair implements `build_a`, `build_b`, `strategies`, and `analytic_bounds`; the registry then makes its metadata available to the shared gallery and payload formatter. A synthetic third-pair contract test checks that the common consumer accepts a new pair without pair-specific branching.

1. Copy [`channels/four_pauli.py`](channels/four_pauli.py) as a worked example, then create `channels/my_pair.py`. Implement the four methods above and give the pair a unique `slug`, `name`, `citation`, and reference `dimension`.
2. Add one registry entry in [`channels/api.py`](channels/api.py), mapping your slug to the new module, exported pair instance, and gallery role. Add claim records to [`claims.json`](claims.json) for every displayed number and reference their IDs from each `Strategy`.
3. Add tests for the formulas, both channel circuits, labels, and registry payload. Run `python -m pytest -q`; then add the new pair to `ALL_SLUGS` and the relevant gallery tests so the shipped surface exercises it too.

This is a small interface, but it is not a promise that all four methods are enough for live execution. The current shared live runner in `quantum/engine.py` is intentionally flagship-specific. A new pair needs its own verified probe, measurement, circuit construction, and execution path before it can be called a live benchmark. The gallery can show theory and circuit metadata without that path.

## What this project does not claim

- It does not claim discovery of the underlying channel-discrimination results. It reproduces and presents prior work; the HURTS result is credited to Lien and Quintino (2026, preprint).
- It does not claim a quantum computational advantage. The small instances used here are classically simulable.
- It does not call analytic values hardware measurements. HELPS `0.875` is explicitly a theoretical ceiling, not a measured result or implemented live strategy.
- It does not imply that entanglement itself is harmful. HURTS, HELPS, and NEUTRAL compare different channel pairs under stated strategies.

The detailed evidence and scope are recorded in [`claims.json`](claims.json) and explained in the [mdBook documentation](docs/src/SUMMARY.md).

## Reproduce the local checks

Use Python 3.12 and the pinned development dependencies. From the repository root:

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

The complete suite checks the analytic fixtures, channel circuits, gallery schema, extension contract, and Qollab bridge behavior using local test backends. One test for the actual Qollab browser runtime is intentionally skipped because that external runtime is not available in a local test run.

To inspect the deterministic reference values without running a backend:

```sh
python - <<'PY'
from channels.api import available_pairs, load_pair

for slug in available_pairs():
    pair = load_pair(slug)
    print(pair.name, pair.analytic_bounds())
PY
```

To check one flagship batch locally, run the engine tests; they use Qiskit Aer and are included in the full suite. No hardware is required for the local checks. A live Qollab run requires the project to be published in Qollab with its selected backend injected by the platform.

## Read the docs

The [Entanglement Trap field guide](docs/src/SUMMARY.md) is an mdBook covering the experiment, channel discrimination, the three cases, evidence labels, limitations, and the extension interface.

```sh
cd docs
mdbook build
mdbook serve --open
```

The generated book is written to `docs/book/` and is not committed. See [docs/README.md](docs/README.md) for book maintenance and validation.

## Acknowledgment

This effort is supported by Qollab & IonQ.

## License

MIT. See [LICENSE](LICENSE).
