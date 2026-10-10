# Run the lab

## Use the published Qollab project

Open the published Entanglement Trap project on Qollab, choose an available backend, and start a project Run. Select a probe, dimension, and shot count, then choose **Play one round**. The project submits one four-circuit batch for the flagship Identity-vs-`V` pair. The batch supports the displayed round and both strategy benchmarks; revealing or comparing results reuses the returned evidence and does not submit another job.

The Qollab runtime supplies the selected backend to the Python bridge. The project reports the backend name and uses the neutral provenance label `qollab-selected-backend`; project code does not guess whether the selected backend is local or remote. A failed run may consume the run's one-job allowance, so the interface asks you to start a new Qollab Run before retrying.

The resource gallery is different: it calls a metadata-only bridge function and submits zero jobs. It lists registered channel pairs, their declared strategies, and best-effort circuit descriptions.

## Run the checks locally

Use Python 3.12. From the repository root:

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

The pinned requirements make the local test environment reproducible; this suite was verified with Python `3.12.14`. It checks science fixtures, Qiskit circuits, exact-statevector results, batch parsing, payload contracts, and the extension interface. The test `test_actual_qollab_browser_runtime_executes_the_batch` is skipped because local tests cannot provide Qollab's browser runtime or its injected backend.

To print the registered pairs and their analytic bounds:

```sh
python - <<'PY'
from channels.api import available_pairs, load_pair

for slug in available_pairs():
    pair = load_pair(slug)
    print(pair.name, pair.analytic_bounds())
PY
```

This command reads formulas from the local implementation. It does not submit a job or produce hardware evidence.

For the flagship pair, the deterministic values include overlap `-0.9921875`, separable success `1.0`, maximally entangled success `0.507781982421875`, and a Helstrom ceiling of `0.5623778102448098`. Their meanings and provenance are explained in [the results chapter](results.md).

## Build this book

Install [mdBook](https://rust-lang.github.io/mdBook/) and run from `docs/`:

```sh
mdbook build
mdbook serve --open
```

The generated HTML is written to `docs/book/`, which is ignored by Git. The book is configured in `docs/book.toml`; its navigation is in `docs/src/SUMMARY.md`.
