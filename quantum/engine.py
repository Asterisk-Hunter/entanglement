"""One-batch flagship engine for the one-query channel-discrimination game.

The flagship remote path is exactly one ``backend.run`` call containing four
named circuits: ``sep_I``, ``sep_V``, ``me_I``, ``me_V``. Every circuit is
padded to the same width. Qiskit is imported at module scope; ``qiskit_aer`` is
never imported here and the backend is always injected by the caller.

This module is deliberately flagship-specific. The resource gallery can share
the ChannelPair metadata API, but any future pair-specific live engine must
implement its own verified measurement contract.
"""

from __future__ import annotations

import random
from typing import Dict, List, Mapping, Sequence, Tuple

from qiskit import QuantumCircuit, transpile

from quantum.results import (
    PROBE_KINDS,
    PROVENANCE_VALUES,
    BatchResult,
    CircuitSpec,
    Outcome,
    Provenance,
    RoundResult,
    StrategyBenchmark,
    success_rate_ci,
)
from quantum.science import is_valid_dimension

__all__ = [
    "BATCH_NAMES",
    "BATCH_PROBE_KINDS",
    "MAX_LIVE_DIMENSION",
    "benchmark_strategy",
    "build_flagship_batch",
    "build_probe_circuit",
    "default_circuit_specs",
    "parse_counts",
    "play_one_round",
    "run_batch",
]

BATCH_NAMES: Tuple[str, ...] = ("sep_I", "sep_V", "me_I", "me_V")
BATCH_PROBE_KINDS: Dict[str, str] = {
    "sep_I": "SEPARABLE",
    "sep_V": "SEPARABLE",
    "me_I": "MAX_ENTANGLEMENT",
    "me_V": "MAX_ENTANGLEMENT",
}
MAX_LIVE_DIMENSION = 256
_FLAGSHIP_PAIR_SLUG = "hurts-identity-v"
_PROBE_LABELS = {"SEPARABLE": "sep", "MAX_ENTANGLEMENT": "me"}


def _require_dimension(d: int) -> int:
    if not is_valid_dimension(d) or d < 2:
        raise ValueError(f"dimension must be a power of two >= 2, got {d!r}")
    return d


def num_system_qubits_for(d: int) -> int:
    return _require_dimension(d).bit_length() - 1


def default_circuit_specs(d: int) -> Tuple[CircuitSpec, ...]:
    _require_dimension(d)
    return tuple(
        CircuitSpec(
            name=name,
            probe_kind=BATCH_PROBE_KINDS[name],
            channel="B" if name.endswith("_V") else "A",
        )
        for name in BATCH_NAMES
    )


def _require_width(d: int, total_qubits: int) -> Tuple[int, int]:
    num_system_qubits = num_system_qubits_for(d)
    if not isinstance(total_qubits, int) or isinstance(total_qubits, bool):
        raise ValueError(f"total_qubits must be an integer, got {total_qubits!r}")
    if total_qubits < 2 * num_system_qubits:
        raise ValueError(
            f"total_qubits ({total_qubits}) must hold the two {num_system_qubits}-qubit "
            f"probe halves at d={d}"
        )
    return num_system_qubits, total_qubits


def _flagship_pair():
    from channels.api import load_pair

    return load_pair(_FLAGSHIP_PAIR_SLUG)


def build_probe_circuit(
    probe: str, channel: str, *, d: int, total_qubits: int
) -> QuantumCircuit:
    """Build one flagship probe/channel/discriminator circuit."""
    if probe not in ("sep", "me"):
        raise ValueError(f"probe must be 'sep' or 'me', got {probe!r}")
    if channel not in ("A", "B"):
        raise ValueError(f"channel must be 'A' or 'B', got {channel!r}")

    num_system_qubits, total_qubits = _require_width(d, total_qubits)
    suffix = "V" if channel == "B" else "I"
    circuit = QuantumCircuit(total_qubits, total_qubits, name=f"{probe}_{suffix}")

    half1 = list(range(num_system_qubits))
    half2 = list(range(num_system_qubits, 2 * num_system_qubits))

    if probe == "sep":
        circuit.h(half1[0])
        circuit.h(half2[0])
    else:
        for qubit in half2:
            circuit.h(qubit)
        for offset, qubit in enumerate(half1):
            circuit.cx(half2[offset], qubit)

    pair = _flagship_pair()
    channel_circuit = (
        pair.build_b(num_system_qubits, total_qubits)
        if channel == "B"
        else pair.build_a(num_system_qubits, total_qubits)
    )
    circuit.compose(channel_circuit, qubits=range(total_qubits), inplace=True)

    if probe == "sep":
        circuit.h(half1[0])
        circuit.h(half2[0])
    else:
        for qubit in half1 + half2:
            circuit.h(qubit)

    circuit.measure(range(total_qubits), range(total_qubits))
    return circuit


def build_flagship_batch(
    d: int = 256, total_qubits: int = 16
) -> List[QuantumCircuit]:
    probe_labels = ("sep", "sep", "me", "me")
    channels = ("A", "B", "A", "B")
    return [
        build_probe_circuit(probe, channel, d=d, total_qubits=total_qubits)
        for probe, channel in zip(probe_labels, channels)
    ]


def _count_key_to_bits(key, total_qubits: int) -> str:
    """Normalize documented Qiskit/provider count-key representations."""
    text = str(key).replace(" ", "")
    if text.startswith(("0x", "0X")):
        value = int(text, 16)
        if value >= 2**total_qubits:
            raise ValueError(
                f"count key {text!r} does not fit in {total_qubits} classical bits"
            )
        return format(value, f"0{total_qubits}b")
    if text.startswith(("0b", "0B")):
        bits = text[2:]
        if not bits or any(bit not in "01" for bit in bits):
            raise ValueError(f"invalid binary count key {text!r}")
        if len(bits) > total_qubits:
            raise ValueError(
                f"count key {text!r} has more than {total_qubits} bits"
            )
        return bits.zfill(total_qubits)
    if len(text) != total_qubits or any(bit not in "01" for bit in text):
        raise ValueError(
            f"count key {text!r} must be a {total_qubits}-bit binary string "
            "or a 0x/0b-prefixed provider key"
        )
    return text


def parse_counts(
    counts: Mapping[str, int],
    total_qubits: int,
    num_system_qubits: int,
    *,
    strict_padding: bool = True,
) -> Dict[Outcome, int]:
    """Split count keys into the two active probe halves, little-endian.

    ``strict_padding=True`` is the audit mode used by regression fixtures: any
    measured ``1`` on an idle padded qubit is an error. Live noisy execution may
    set it to ``False`` so readout noise on logically unused qubits cannot kill
    the d=64 fallback; padding bits are then ignored when forming the outcome.
    """
    probe_width = 2 * num_system_qubits
    if probe_width > total_qubits:
        raise ValueError(
            f"probe register ({probe_width} qubits) exceeds total_qubits ({total_qubits})"
        )
    parsed: Dict[Outcome, int] = {}
    for key, count in counts.items():
        text = _count_key_to_bits(key, total_qubits)
        half1 = text[total_qubits - num_system_qubits :]
        half2 = text[total_qubits - probe_width : total_qubits - num_system_qubits]
        padding = text[: total_qubits - probe_width]
        if strict_padding and "1" in padding:
            raise ValueError(
                f"idle padding bits are not zero in count key {text!r}: "
                f"padding={padding!r}"
            )
        outcome = (tuple(half2), tuple(half1))
        parsed[outcome] = parsed.get(outcome, 0) + count
    return parsed


def _extract_counts(result, names: Sequence[str]) -> Tuple[Dict[str, dict], str]:
    """Map backend output to local names, preferring Qiskit normalization."""
    get_counts = getattr(result, "get_counts", None)
    experiments = list(getattr(result, "results", []) or [])
    if callable(get_counts) and experiments:
        named = [getattr(experiment.header, "name", None) for experiment in experiments]
        if all(name in names for name in named) and len(set(named)) == len(named):
            return ({name: dict(get_counts(name)) for name in names}, "by-name")

    if len(experiments) != len(names):
        raise ValueError(
            f"backend returned {len(experiments)} experiments for {len(names)} "
            "circuits; cannot map results"
        )

    if callable(get_counts):
        try:
            return (
                {name: dict(get_counts(index)) for index, name in enumerate(names)},
                "by-position",
            )
        except (KeyError, IndexError, TypeError, ValueError):
            pass

    return (
        {
            name: dict(getattr(experiment.data, "counts", {}))
            for name, experiment in zip(names, experiments)
        },
        "by-position",
    )


def _backend_name(backend) -> str:
    value = getattr(backend, "name", None)
    if callable(value):
        try:
            value = value()
        except TypeError:
            value = None
    if value in (None, ""):
        return backend.__class__.__name__ or "unknown-backend"
    return str(value)


def run_batch(
    backend,
    shots: int,
    d: int = 256,
    *,
    total_qubits: int = 16,
    provenance: str = Provenance.LIVE_LOCAL,
    strict_padding: bool = True,
) -> BatchResult:
    """Execute the verified flagship batch in exactly one backend job."""
    if provenance not in (Provenance.LIVE_REMOTE, Provenance.LIVE_LOCAL):
        raise ValueError(
            "run_batch produces live results; provenance must be "
            f"{Provenance.LIVE_REMOTE!r} or {Provenance.LIVE_LOCAL!r}, got "
            f"{provenance!r}"
        )
    _require_dimension(d)
    if d > MAX_LIVE_DIMENSION:
        raise ValueError(
            f"d={d} exceeds the maximum live dimension ({MAX_LIVE_DIMENSION}); "
            "it may only be served as verified precomputed data"
        )
    num_system_qubits, _ = _require_width(d, total_qubits)
    if not isinstance(shots, int) or isinstance(shots, bool) or shots < 1:
        raise ValueError(f"shots must be a positive integer, got {shots!r}")

    pair = _flagship_pair()
    circuits = build_flagship_batch(d, total_qubits)
    # The built-in simulator does not decompose MCX automatically. Translate
    # to portable abstract gates before submission, retaining the register and
    # measurement layout. One process also works in Qollab's browser runtime.
    circuits = transpile(
        circuits,
        basis_gates=["rx", "ry", "rz", "cx"],
        optimization_level=0,
        num_processes=1,
    )
    job = backend.run(circuits, shots=shots)
    result = job.result()
    counts, mapping = _extract_counts(result, BATCH_NAMES)
    outcomes = {
        name: parse_counts(
            counts[name],
            total_qubits,
            num_system_qubits,
            strict_padding=strict_padding,
        )
        for name in BATCH_NAMES
    }
    return BatchResult(
        pair_slug=pair.slug,
        dimension=d,
        total_qubits=total_qubits,
        num_system_qubits=num_system_qubits,
        shots=shots,
        circuits=default_circuit_specs(d),
        counts={name: dict(counts[name]) for name in BATCH_NAMES},
        outcomes=outcomes,
        provenance=provenance,
        backend_name=_backend_name(backend),
        result_mapping=mapping,
    )


def _guess_from_outcome(outcome: Outcome) -> str:
    return "A" if outcome[0] == outcome[1] else "B"


def play_one_round(
    backend,
    *,
    probe_kind: str,
    shots: int = 1,
    d: int = 256,
    total_qubits: int = 16,
    rng_seed: int | None = None,
) -> RoundResult:
    if probe_kind not in PROBE_KINDS:
        raise ValueError(f"probe_kind must be one of {PROBE_KINDS}, got {probe_kind!r}")
    if shots != 1:
        raise ValueError("a literal one-round execution must use exactly one shot")
    _require_dimension(d)
    num_system_qubits, _ = _require_width(d, total_qubits)

    rng = random.Random(rng_seed)
    hidden_channel = rng.choice(("A", "B"))
    probe = _PROBE_LABELS[probe_kind]
    circuit = build_probe_circuit(
        probe, hidden_channel, d=d, total_qubits=total_qubits
    )
    counts, _ = _extract_counts(
        backend.run([circuit], shots=1).result(), [circuit.name]
    )
    parsed = parse_counts(counts[circuit.name], total_qubits, num_system_qubits)
    outcome = next(iter(parsed))
    guess = _guess_from_outcome(outcome)
    return RoundResult(
        hidden_channel=hidden_channel,
        guess=guess,
        outcome=outcome,
        won=guess == hidden_channel,
    )


def _analytic_values(
    pair, probe_kind: str, dimension: int
) -> Tuple[float, float, str]:
    bounds = pair.analytic_bounds_for(dimension)
    if probe_kind == "SEPARABLE":
        value = bounds["separable"]
        ceiling = bounds["separable"]
    else:
        value = bounds["max_entanglement_simple"]
        ceiling = bounds["helstrom_ceiling"]
    return float(value), float(ceiling), "ANALYTIC"


def benchmark_strategy(batch: BatchResult, strategy_slug: str) -> StrategyBenchmark:
    if batch.provenance not in PROVENANCE_VALUES:
        raise ValueError(f"unexpected provenance {batch.provenance!r}")
    from channels.api import load_pair

    pair = load_pair(batch.pair_slug)
    strategies = {strategy.slug: strategy for strategy in pair.strategies()}
    strategy = strategies[strategy_slug]
    probe_kind = strategy.probe_kind
    names = tuple(
        spec.name for spec in batch.circuits if spec.probe_kind == probe_kind
    )
    if len(names) != 2:
        raise ValueError(f"expected two circuits for {probe_kind}, got {names}")

    correct = 0
    for spec_name in names:
        channel = batch.spec_for(spec_name).channel
        for outcome, count in batch.outcomes_for(spec_name).items():
            if _guess_from_outcome(outcome) == channel:
                correct += count

    trials = 2 * batch.shots
    rate = correct / trials if trials else 0.0
    ci_low, ci_high = success_rate_ci(correct, trials)
    analytic, ceiling, bound_kind = _analytic_values(
        pair, probe_kind, batch.dimension
    )
    return StrategyBenchmark(
        pair_slug=batch.pair_slug,
        strategy_slug=strategy_slug,
        probe_kind=probe_kind,
        dimension=batch.dimension,
        trials=trials,
        shots_per_channel=batch.shots,
        correct_trials=correct,
        empirical_rate=rate,
        ci_low=ci_low,
        ci_high=ci_high,
        analytic_value=analytic,
        ceiling=ceiling,
        provenance=batch.provenance,
        bound_kind=bound_kind,
        extra={"strategy_label": strategy.label},
    )
