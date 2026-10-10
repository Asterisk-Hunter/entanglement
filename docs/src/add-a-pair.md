# How to add a channel pair

The gallery uses a shared `ChannelPair` interface. A new implementation can provide the science metadata and channel circuits without changing the generic payload formatter. The present interface test creates a synthetic third pair and verifies that serialization and circuit construction use the shared helpers.

## 1. Implement the pair

Create `channels/my_pair.py`. `channels/four_pauli.py` is the most complete worked example: it includes formulas, circuit builders, strategy records, and tests for an attaining measurement.

Subclass `ChannelPair` and provide:

```python
name = "My channel pair"
slug = "my-channel-pair"
citation = "A precise source or derivation for this comparison."
dimension = 2

def build_a(self, num_system_qubits: int, total_qubits: int) -> QuantumCircuit:
    ...

def build_b(self, num_system_qubits: int, total_qubits: int) -> QuantumCircuit:
    ...

def strategies(self) -> tuple[Strategy, ...]:
    ...

def analytic_bounds(self) -> dict[str, float]:
    ...
```

The circuit builders must reject a padded register that is narrower than the system they need. Keep `build_a` and `build_b` focused on the channel action; probe preparation and measurement belong to the experiment strategy. Return strategy records with stable slugs, a supported probe kind, a correct evidence kind, the analytic value, and claim IDs.

## 2. Register and document its claims

Add a mapping to `_PAIR_REGISTRY` in `channels/api.py` with the module path, exported singleton name, and gallery role. Add each displayed claim to `claims.json`, including the value, formula, dimension, provenance, and whether it is safe for the demo. Link the claim IDs from the relevant `Strategy` objects.

`available_pairs()` and `registered_pair_payloads()` then discover the pair through the common schema. Gallery discovery is lazy and does not run a backend job. A circuit description is best-effort: optional dependencies may be missing in the Qollab runtime, while the science metadata remains available.

## 3. Verify it

Add tests for the formulas against an independent derivation or matrix calculation, channel circuits, strategy labels, claim IDs, and payload. Include an exact-statevector test if you claim an executable measurement attains an optimum. Add the slug to the shared channel tests.

Run:

```sh
python -m pytest -q
```

The existing `test_synthetic_pair_needs_no_loader_consumer_change` proves only the shared interface and generic payload path. It does not prove a new pair is in the registry, rendered in the browser, or executable on a selected backend. The extension process is designed to be a short code change, but the time required depends on the experiment and its verification; no fixed completion time is guaranteed.

## Live execution is a separate step

The current `quantum.engine` constructs and interprets the four-circuit HURTS batch. Registering a pair makes it discoverable in the theory gallery; it does not turn it into a live benchmark. A live strategy needs an explicit preparation and measurement circuit, validated result parsing, tests against the pair's analytic probabilities, and a deliberate bridge/UI integration. Until those exist, label it as analytic metadata or a theoretical ceiling.
