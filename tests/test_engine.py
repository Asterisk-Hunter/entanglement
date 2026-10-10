"""Regression tests for the one-batch flagship quantum engine.

Task 3 scope: four-circuit batch construction, single-invocation execution,
little-endian count parsing, idle-padding verification, explicit provenance,
and unconfusable round-versus-benchmark result types.

Every backend here is a fake. Nothing in this file imports qiskit_aer.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from qiskit import QuantumCircuit

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from channels.api import load_pair  # noqa: E402
from quantum.engine import (  # noqa: E402
    BATCH_NAMES,
    MAX_LIVE_DIMENSION,
    benchmark_strategy,
    build_flagship_batch,
    build_probe_circuit,
    parse_counts,
    play_one_round,
    run_batch,
)
from quantum.results import (  # noqa: E402
    PROVENANCE_VALUES,
    BatchResult,
    CircuitSpec,
    Provenance,
    RoundResult,
    StrategyBenchmark,
    success_rate_ci,
)
from quantum.science import (  # noqa: E402
    SEPARABLE_SUCCESS,
    helstrom_ceiling,
    overlap,
    simple_success,
)

HURTS_SLUG = "hurts-identity-v"
PAIR = load_pair(HURTS_SLUG)

TOTAL_QUBITS = 16
FLAGGESHIP_D = 256
FLAGGESHIP_N = 8

# Frozen flagship values, read from the Task 1 kernel rather than restated.
FLAGSHIP_OVERLAP = -0.9921875
FLAGSHIP_SIMPLE = 0.507781982421875
FLAGSHIP_CEILING = 0.5623778102448098
# Printed spec figure that must never surface anywhere in engine output.
UNSAFE_PRINTED_FIGURE = 0.5078125


# --------------------------------------------------------------- fake backend


class _Counts:
    def __init__(self, counts: dict) -> None:
        self.counts = counts


class _Header:
    def __init__(self, name: str | None) -> None:
        self.name = name


class _ExperimentResult:
    def __init__(self, name: str | None, counts: dict) -> None:
        self.header = _Header(name)
        self.data = _Counts(counts)


class _FakeResult:
    """Mimics a backend result object, with or without circuit names."""

    def __init__(self, entries: list[tuple[str | None, dict]]) -> None:
        self.results = [
            _ExperimentResult(name, counts) for name, counts in entries
        ]

    def get_counts(self, name: str) -> dict:
        for experiment in self.results:
            if experiment.header.name == name:
                return experiment.data.counts
        raise KeyError(name)


class _PositionalResult:
    """Positional-only result: circuit names are unavailable."""

    def __init__(self, entries: list[tuple[str | None, dict]]) -> None:
        self.results = [
            _ExperimentResult(None, counts) for _, counts in entries
        ]


class _FakeJob:
    def __init__(self, result) -> None:
        self._result = result

    def result(self):
        return self._result


class _FakeBackend:
    """Records every `run` invocation so the one-call contract can be pinned."""

    def __init__(self, counts_by_name: dict, mapping: str = "by-name") -> None:
        self.counts_by_name = counts_by_name
        self.mapping = mapping
        self.run_calls: list[tuple[list, dict]] = []
        self.name = "fake-backend"

    def run(self, circuits, **kwargs):
        self.run_calls.append((list(circuits), dict(kwargs)))
        entries = [
            (name, self.counts_by_name[name])
            for name in (circuit.name for circuit in circuits)
        ]
        if self.mapping == "by-name":
            return _FakeJob(_FakeResult(entries))
        return _FakeJob(_PositionalResult(entries))


# ------------------------------------------------------------- ideal fixtures


def _bit_key(total_qubits: int, set_qubits) -> str:
    """Counts key for `set_qubits`, honouring Qiskit little-endian ordering."""
    chars = ["0"] * total_qubits
    for qubit in set_qubits:
        chars[total_qubits - 1 - qubit] = "1"
    return "".join(chars)


def _match_key(total_qubits: int, num_system_qubits: int) -> str:
    """Outcome where both halves measure the same X-basis string of zeros."""
    return _bit_key(total_qubits, set())


def _mismatch_key(total_qubits: int, num_system_qubits: int) -> str:
    """Outcome where the halves differ: only the top qubit of half 2 is set."""
    return _bit_key(total_qubits, {2 * num_system_qubits - 1})


def _ideal_separable_counts(
    total_qubits: int, num_system_qubits: int, channel_b: bool, shots: int
) -> dict:
    """Deterministic separable outcome, verified against exact simulation.

    Channel A reads every probe qubit `0`; channel `B` flips only qubit 0 of the
    channel half, so the two halves disagree.
    """
    qubits = {0} if channel_b else set()
    return {_bit_key(total_qubits, qubits): shots}


def _ideal_maxent_counts(
    total_qubits: int, num_system_qubits: int, channel_b: bool, shots: int
) -> dict:
    """Max-ent outcomes split by whether the two halves agree.

    Under channel A the halves always agree. Under channel B they agree with
    probability `overlap(d)**2`, using the Task 1 kernel.
    """
    dimension = 2**num_system_qubits
    if not channel_b:
        agreeing = shots
    else:
        agreeing = round(shots * overlap(dimension) ** 2)
    disagreeing = shots - agreeing
    counts = {}
    if agreeing:
        counts[_match_key(total_qubits, num_system_qubits)] = agreeing
    if disagreeing:
        counts[_mismatch_key(total_qubits, num_system_qubits)] = disagreeing
    return counts


def flagship_counts(shots: int = 1000) -> dict:
    return {
        "sep_I": _ideal_separable_counts(TOTAL_QUBITS, FLAGGESHIP_N, False, shots),
        "sep_V": _ideal_separable_counts(TOTAL_QUBITS, FLAGGESHIP_N, True, shots),
        "me_I": _ideal_maxent_counts(TOTAL_QUBITS, FLAGGESHIP_N, False, shots),
        "me_V": _ideal_maxent_counts(TOTAL_QUBITS, FLAGGESHIP_N, True, shots),
    }


# ------------------------------------------------------------ batch shape


def test_batch_has_exactly_four_circuits_in_order() -> None:
    batch = build_flagship_batch()
    assert [circuit.name for circuit in batch] == ["sep_I", "sep_V", "me_I", "me_V"]
    assert BATCH_NAMES == ("sep_I", "sep_V", "me_I", "me_V")


def test_batch_circuits_are_quantum_circuits_of_exactly_16_qubits() -> None:
    for circuit in build_flagship_batch():
        assert isinstance(circuit, QuantumCircuit)
        assert circuit.num_qubits == TOTAL_QUBITS
        assert circuit.num_clbits == TOTAL_QUBITS


@pytest.mark.parametrize("d", [4, 16, 64, 256])
def test_batch_width_is_independent_of_dimension(d: int) -> None:
    num_system_qubits = d.bit_length() - 1
    for circuit in build_flagship_batch(d, TOTAL_QUBITS):
        assert circuit.num_qubits == TOTAL_QUBITS
        assert circuit.num_qubits >= 2 * num_system_qubits


def test_batch_rejects_non_power_of_two_dimension() -> None:
    with pytest.raises(ValueError):
        build_flagship_batch(3)
    with pytest.raises(ValueError):
        build_flagship_batch(0)


def test_batch_rejects_total_qubits_below_the_probe_register() -> None:
    with pytest.raises(ValueError):
        build_flagship_batch(256, 15)
    with pytest.raises(ValueError):
        build_flagship_batch(1024, 16)


def test_batch_uses_only_the_probe_qubits() -> None:
    """At d=64 the four highest qubits must stay untouched."""
    num_system_qubits = 6
    for circuit in build_flagship_batch(64, TOTAL_QUBITS):
        touched = {
            circuit.find_bit(qubit).index
            for instruction in circuit.data
            if instruction.operation.name not in ("barrier", "measure")
            for qubit in instruction.qubits
        }
        assert touched <= set(range(2 * num_system_qubits))


def test_probe_circuit_builder_is_reusable_for_one_round() -> None:
    circuit = build_probe_circuit("me", "B", d=256, total_qubits=TOTAL_QUBITS)
    assert circuit.num_qubits == TOTAL_QUBITS
    assert circuit.name == "me_V"


# ------------------------------------------------------- single batched call


def test_run_batch_calls_backend_run_exactly_once_with_four_circuits() -> None:
    backend = _FakeBackend(flagship_counts())
    result = run_batch(backend, shots=1000, d=FLAGGESHIP_D)
    assert isinstance(result, BatchResult)
    assert len(backend.run_calls) == 1
    circuits, kwargs = backend.run_calls[0]
    assert len(circuits) == 4
    assert [circuit.name for circuit in circuits] == ["sep_I", "sep_V", "me_I", "me_V"]
    assert kwargs["shots"] == 1000


def test_run_batch_keeps_names_in_local_metadata() -> None:
    backend = _FakeBackend(flagship_counts())
    result = run_batch(backend, shots=1000, d=FLAGGESHIP_D)
    assert [spec.name for spec in result.circuits] == list(BATCH_NAMES)
    assert result.result_mapping == "by-name"
    for spec in result.circuits:
        assert spec.channel == ("B" if spec.name.endswith("_V") else "A")
        assert spec.probe_kind in {"SEPARABLE", "MAX_ENTANGLEMENT"}


def test_run_batch_maps_positional_results_when_names_are_absent() -> None:
    backend = _FakeBackend(flagship_counts(), mapping="by-position")
    result = run_batch(backend, shots=1000, d=FLAGGESHIP_D)
    assert len(backend.run_calls) == 1
    assert result.result_mapping == "by-position"
    assert [spec.name for spec in result.circuits] == list(BATCH_NAMES)
    assert set(result.counts) == set(BATCH_NAMES)
    # The counts must land on the same circuits as in the named path.
    named = run_batch(_FakeBackend(flagship_counts(shots=1000)), shots=1000, d=FLAGGESHIP_D)
    assert dict(result.counts) == dict(named.counts)


def test_run_batch_rejects_a_backend_returning_the_wrong_circuit_count() -> None:
    counts = flagship_counts(shots=100)
    backend = _FakeBackend(counts, mapping="by-position")
    original = backend.run

    def truncated(circuits, **kwargs):
        job = original(circuits, **kwargs)
        job._result.results = job._result.results[:3]
        return job

    backend.run = truncated
    with pytest.raises(ValueError):
        run_batch(backend, shots=100, d=FLAGGESHIP_D)


# ------------------------------------------------------ endianness / padding


def test_qubit_zero_is_the_rightmost_count_character() -> None:
    """Key "0001" sets qubit 0, which belongs to half 1."""
    counts = {"0001": 5}
    parsed = parse_counts(counts, total_qubits=4, num_system_qubits=1)
    assert list(parsed) == [(("0",), ("1",))]
    half2, half1 = next(iter(parsed))
    assert half1 == ("1",), "qubit 0 must be the rightmost character"
    assert half2 == ("0",)


def test_padding_bits_are_zero_in_the_golden_ideal_fixture() -> None:
    """d=4 in a 16-qubit register: the 12 padding bits must read 0."""
    num_system_qubits = 2
    for channel_b in (False, True):
        counts = _ideal_separable_counts(TOTAL_QUBITS, num_system_qubits, channel_b, 64)
        key = next(iter(counts))
        parsed = parse_counts(counts, TOTAL_QUBITS, num_system_qubits)
        assert key[:12] == "0" * 12, "idle padding must read 0"
        assert len(parsed) == 1
        (outcome,) = list(parsed)
        # Channel A leaves the halves equal, channel B makes them differ.
        assert (outcome[0] == outcome[1]) is (not channel_b)


def test_nonzero_padding_bits_are_rejected() -> None:
    num_system_qubits = 2
    # Qubits 0..3 are the probe; qubit 4 sits in the idle padding region.
    key = "0000000000011111"[:11] + "1" + "1111"
    assert len(key) == 16
    with pytest.raises(ValueError) as excinfo:
        parse_counts({key: 10}, TOTAL_QUBITS, num_system_qubits)
    assert "padding" in str(excinfo.value).lower()


def test_count_key_width_is_validated() -> None:
    with pytest.raises(ValueError):
        parse_counts({"001": 5}, total_qubits=4, num_system_qubits=1)
    with pytest.raises(ValueError):
        parse_counts({"00001": 5}, total_qubits=4, num_system_qubits=1)


def test_run_batch_rejects_counts_with_nonzero_padding() -> None:
    """d=64 in a 16-qubit register leaves four idle padding bits."""
    counts = {
        "sep_I": {"0001" + "1" * 12: 1000},
        "sep_V": {"0000" + "0" * 12: 1000},
        "me_I": {"0000" + "0" * 12: 1000},
        "me_V": {"0000" + "1" + "0" * 11: 1000},
    }
    with pytest.raises(ValueError):
        run_batch(_FakeBackend(counts), shots=1000, d=64)


# -------------------------------------------------------------- provenance


def test_provenance_values_are_explicit() -> None:
    assert Provenance.LIVE_REMOTE == "live-remote"
    assert Provenance.LIVE_LOCAL == "live-local"
    assert Provenance.PRECOMPUTED == "precomputed"
    assert set(PROVENANCE_VALUES) == {
        "live-remote",
        "live-local",
        "precomputed",
    }


def test_run_batch_provenance_is_live_by_default_and_can_be_remote() -> None:
    local = run_batch(_FakeBackend(flagship_counts(shots=100)), shots=100, d=FLAGGESHIP_D)
    assert local.provenance == Provenance.LIVE_LOCAL
    assert local.is_live is True
    remote = run_batch(
        _FakeBackend(flagship_counts()),
        shots=100,
        d=FLAGGESHIP_D,
        provenance=Provenance.LIVE_REMOTE,
    )
    assert remote.provenance == Provenance.LIVE_REMOTE
    assert remote.is_live is True


def test_unknown_provenance_is_rejected() -> None:
    with pytest.raises(ValueError):
        run_batch(
            _FakeBackend(flagship_counts()),
            shots=100,
            d=FLAGGESHIP_D,
            provenance="cached",
        )


def test_precomputed_result_never_reports_itself_as_live() -> None:
    precomputed = BatchResult.from_precomputed(
        counts=flagship_counts(),
        shots=1000,
        dimension=FLAGGESHIP_D,
        total_qubits=TOTAL_QUBITS,
        pair_slug=HURTS_SLUG,
    )
    assert precomputed.provenance == Provenance.PRECOMPUTED
    assert precomputed.is_live is False
    assert precomputed.backend_name == "precomputed-fixture"
    assert json.loads(json.dumps(precomputed.to_payload()))["provenance"] == "precomputed"


def test_run_batch_refuses_to_claim_precomputed_provenance() -> None:
    with pytest.raises(ValueError):
        run_batch(
            _FakeBackend(flagship_counts()),
            shots=100,
            d=FLAGGESHIP_D,
            provenance=Provenance.PRECOMPUTED,
        )


def test_no_live_path_beyond_the_maximum_live_dimension() -> None:
    assert MAX_LIVE_DIMENSION == 256
    with pytest.raises(ValueError):
        run_batch(_FakeBackend(flagship_counts(shots=10)), shots=10, d=1024, total_qubits=32)
    with pytest.raises(ValueError):
        run_batch(_FakeBackend(flagship_counts(shots=10)), shots=10, d=512, total_qubits=32)


def test_precomputed_dimension_above_the_live_limit_is_allowed() -> None:
    precomputed = BatchResult.from_precomputed(
        counts={name: {"0" * 32: 5} for name in BATCH_NAMES},
        shots=5,
        dimension=1024,
        total_qubits=32,
        pair_slug=HURTS_SLUG,
    )
    assert precomputed.dimension == 1024
    assert precomputed.is_live is False


# ------------------------------------------------------------- round schema


def test_round_result_carries_only_the_literal_round_fields() -> None:
    from dataclasses import fields

    names = [field.name for field in fields(RoundResult)]
    assert names == ["hidden_channel", "guess", "outcome", "won"]
    assert "rate" not in names
    assert "trials" not in names
    assert "probabilit" not in " ".join(names)


def test_play_one_round_returns_a_single_won_flag() -> None:
    backend = _FakeBackend(flagship_counts())
    round_result = play_one_round(
        backend,
        probe_kind="MAX_ENTANGLEMENT",
        shots=1,
        d=FLAGGESHIP_D,
        rng_seed=7,
    )
    assert isinstance(round_result, RoundResult)
    assert round_result.hidden_channel in {"A", "B"}
    assert round_result.guess in {"A", "B"}
    assert isinstance(round_result.won, bool)
    assert len(round_result.outcome) == 2
    assert all(isinstance(half, tuple) for half in round_result.outcome)
    # A single round makes exactly one backend call with one circuit.
    assert len(backend.run_calls) == 1
    assert len(backend.run_calls[0][0]) == 1


def test_play_one_round_outcome_is_consistent_with_the_won_flag() -> None:
    backend = _FakeBackend(flagship_counts())
    for seed in range(6):
        round_result = play_one_round(
            backend,
            probe_kind="SEPARABLE",
            shots=1,
            d=FLAGGESHIP_D,
            rng_seed=seed,
        )
        halves_agree = round_result.outcome[0] == round_result.outcome[1]
        assert round_result.guess == ("A" if halves_agree else "B")
        assert round_result.won == (round_result.guess == round_result.hidden_channel)


def test_play_one_round_is_reproducible_for_a_fixed_seed() -> None:
    first = play_one_round(
        _FakeBackend(flagship_counts()),
        probe_kind="MAX_ENTANGLEMENT",
        shots=1,
        d=256,
        rng_seed=11,
    )
    second = play_one_round(
        _FakeBackend(flagship_counts()),
        probe_kind="MAX_ENTANGLEMENT",
        shots=1,
        d=256,
        rng_seed=11,
    )
    assert first == second


def test_play_one_round_rejects_unknown_probe_kind() -> None:
    with pytest.raises(ValueError):
        play_one_round(
            _FakeBackend(flagship_counts()),
            probe_kind="PARTIAL",
            shots=1,
            d=256,
            rng_seed=3,
        )


# -------------------------------------------------------- benchmark schema


def test_benchmark_fields_keep_empirical_analytic_and_ceiling_separate() -> None:
    from dataclasses import fields

    names = {field.name for field in fields(StrategyBenchmark)}
    assert {
        "trials",
        "empirical_rate",
        "ci_low",
        "ci_high",
        "analytic_value",
        "ceiling",
    } <= names
    assert "won" not in names
    assert "outcome" not in names


def test_benchmark_max_entanglement_matches_the_kernel() -> None:
    result = run_batch(_FakeBackend(flagship_counts(shots=100000)), shots=100000)
    benchmark = benchmark_strategy(result, "hurts-max-entanglement")
    assert isinstance(benchmark, StrategyBenchmark)
    assert benchmark.empirical_rate == pytest.approx(
        simple_success(FLAGGESHIP_D), abs=5e-4
    )
    assert benchmark.analytic_value == pytest.approx(FLAGSHIP_SIMPLE, abs=1e-15)
    assert benchmark.ceiling == pytest.approx(FLAGSHIP_CEILING, abs=1e-15)
    assert benchmark.analytic_value == pytest.approx(
        simple_success(FLAGGESHIP_D), abs=1e-15
    )
    assert benchmark.ceiling == pytest.approx(
        helstrom_ceiling(FLAGGESHIP_D), abs=1e-15
    )
    assert benchmark.provenance == Provenance.LIVE_LOCAL


def test_benchmark_separable_is_perfect() -> None:
    result = run_batch(_FakeBackend(flagship_counts(shots=1000)), shots=1000)
    benchmark = benchmark_strategy(result, "hurts-separable")
    assert benchmark.empirical_rate == pytest.approx(SEPARABLE_SUCCESS, abs=1e-12)
    assert benchmark.analytic_value == pytest.approx(SEPARABLE_SUCCESS, abs=1e-15)
    assert benchmark.ceiling == pytest.approx(SEPARABLE_SUCCESS, abs=1e-15)
    assert benchmark.empirical_rate > benchmark_benchmark_max_ent(result)


def benchmark_benchmark_max_ent(result: BatchResult) -> float:
    return benchmark_strategy(result, "hurts-max-entanglement").empirical_rate


def test_benchmark_reports_trials_and_a_valid_confidence_interval() -> None:
    result = run_batch(_FakeBackend(flagship_counts(shots=4000)), shots=4000)
    benchmark = benchmark_strategy(result, "hurts-max-entanglement")
    assert benchmark.trials == 8000
    assert benchmark.shots_per_channel == 4000
    assert 0.0 <= benchmark.ci_low <= benchmark.empirical_rate <= benchmark.ci_high <= 1.0
    assert benchmark.ci_high - benchmark.ci_low < 0.05


def test_benchmark_confidence_interval_is_not_the_analytic_value() -> None:
    """The interval must be a sampling band around the empirical rate only."""
    result = run_batch(_FakeBackend(flagship_counts(shots=64)), shots=64)
    benchmark = benchmark_strategy(result, "hurts-max-entanglement")
    assert benchmark.analytic_value == pytest.approx(FLAGSHIP_SIMPLE, abs=1e-15)
    assert benchmark.ceiling == pytest.approx(FLAGSHIP_CEILING, abs=1e-15)
    assert abs(benchmark.ci_low - benchmark.ci_high) > 0.0
    assert benchmark.empirical_rate >= benchmark.ci_low
    assert benchmark.empirical_rate <= benchmark.ci_high


def test_success_rate_ci_is_a_normal_approximation_clamped_to_the_unit_interval() -> None:
    low, high = success_rate_ci(correct=0, trials=10)
    assert low == 0.0
    assert 0.0 < high < 1.0
    low, high = success_rate_ci(correct=10, trials=10)
    assert high == 1.0
    assert 0.0 < low < 1.0
    low, high = success_rate_ci(correct=5, trials=10)
    assert low < 0.5 < high
    assert success_rate_ci(correct=5, trials=0)[0] == 0.0


def test_benchmark_rejects_an_unknown_strategy() -> None:
    result = run_batch(_FakeBackend(flagship_counts(shots=100)), shots=100)
    with pytest.raises(KeyError):
        benchmark_strategy(result, "hurts-unknown")


def test_benchmark_rejects_an_unknown_pair_slug() -> None:
    result = run_batch(_FakeBackend(flagship_counts(shots=100)), shots=100)
    stale = BatchResult(
        pair_slug="no-such-pair",
        dimension=result.dimension,
        total_qubits=result.total_qubits,
        num_system_qubits=result.num_system_qubits,
        shots=result.shots,
        circuits=result.circuits,
        counts=result.counts,
        outcomes=result.outcomes,
        provenance=result.provenance,
        backend_name=result.backend_name,
        result_mapping=result.result_mapping,
    )
    with pytest.raises(KeyError):
        benchmark_strategy(stale, "hurts-max-entanglement")


def test_benchmark_payload_is_json_serializable_and_labelled() -> None:
    result = run_batch(_FakeBackend(flagship_counts(shots=100)), shots=100)
    payload = benchmark_strategy(result, "hurts-max-entanglement").to_payload()
    assert json.loads(json.dumps(payload)) == payload
    assert payload["empirical_kind"] == "EMPIRICAL"
    assert payload["analytic_kind"] == "ANALYTIC"
    assert payload["ceiling_kind"] == "THEORETICAL_CEILING"
    assert payload["bound_kind"] in ("ANALYTIC", "THEORETICAL_CEILING")


def test_benchmark_bound_kinds_are_never_empirical_for_analytic_values() -> None:
    result = run_batch(_FakeBackend(flagship_counts(shots=100)), shots=100)
    for slug in ("hurts-separable", "hurts-max-entanglement"):
        payload = benchmark_strategy(result, slug).to_payload()
        assert payload["analytic_kind"] == "ANALYTIC"
        assert payload["ceiling_kind"] == "THEORETICAL_CEILING"


# ------------------------------------------------------- fixture integrity


def test_engine_output_never_surfaces_the_superseded_printed_figure() -> None:
    result = run_batch(_FakeBackend(flagship_counts(shots=100)), shots=100)
    payloads = [result.to_payload()]
    for slug in ("hurts-separable", "hurts-max-entanglement"):
        payloads.append(benchmark_strategy(result, slug).to_payload())
    blob = json.dumps(payloads)
    assert str(UNSAFE_PRINTED_FIGURE) not in blob
    assert FLAGSHIP_SIMPLE in [p.get("analytic_value") for p in payloads[1:]]


def test_pair_analytic_bounds_are_the_only_source_of_analytic_values() -> None:
    result = run_batch(_FakeBackend(flagship_counts(shots=100)), shots=100)
    bounds = PAIR.analytic_bounds()
    max_ent = benchmark_strategy(result, "hurts-max-entanglement")
    separable = benchmark_strategy(result, "hurts-separable")
    assert max_ent.analytic_value == pytest.approx(
        bounds["max_entanglement_simple"], abs=1e-15
    )
    assert max_ent.ceiling == pytest.approx(bounds["helstrom_ceiling"], abs=1e-15)
    assert separable.analytic_value == pytest.approx(bounds["separable"], abs=1e-15)


def test_frozen_overlap_value_still_matches_the_spec() -> None:
    assert overlap(FLAGGESHIP_D) == pytest.approx(FLAGSHIP_OVERLAP, abs=1e-15)


# ----------------------------------------------------------- import hygiene


def test_importing_the_engine_does_not_pull_in_qiskit_aer() -> None:
    """HARD RULE: no import-time qiskit_aer anywhere in the engine chain."""
    script = (
        "import sys; import quantum.engine as e; "
        "print([m for m in sys.modules if m.startswith('qiskit_aer')])"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip().endswith("[]"), completed.stdout


def test_engine_modules_avoid_novelty_language() -> None:
    forbidden = (
        "we discovered",
        "quantum advantage",
        "quantum computational advantage",
        "breakthrough",
    )
    for module in ("quantum/engine.py", "quantum/results.py"):
        text = (REPO_ROOT / module).read_text(encoding="utf-8").lower()
        for phrase in forbidden:
            index = text.find(phrase)
            while index >= 0:
                prefix = text[max(0, index - 12) : index]
                assert prefix.rstrip().endswith(("no", "not", "never")), (
                    f"{module} contains {phrase!r} (prefix {prefix!r})"
                )
                index = text.find(phrase, index + len(phrase))


# ------------------------------------------------------ exact-state physics


def _exact_outcome_probabilities(circuit) -> dict:
    """Exact outcome probabilities from a statevector (no sampling, no Aer)."""
    from qiskit.quantum_info import Statevector

    bare = circuit.remove_final_measurements(inplace=False)
    amplitudes = np.asarray(Statevector.from_instruction(bare).data).reshape(-1)
    probabilities = np.abs(amplitudes) ** 2
    counts = {}
    for index, value in enumerate(probabilities):
        if value > 1e-12:
            counts[format(index, "0%db" % circuit.num_qubits)] = float(value)
    return counts


@pytest.mark.parametrize("d", [4, 16, 64, 256])
def test_built_circuits_attain_the_kernel_values_exactly(d: int) -> None:
    """Exact simulation must reproduce the analytic values, not just the fakes.

    The separable probe must decide deterministically at 1.0, and the maximally
    entangled probe must land on `1 - overlap(d)**2 / 2` while staying under the
    Helstrom ceiling.
    """
    num_system_qubits = d.bit_length() - 1
    outcomes = {
        circuit.name: parse_counts(
            _exact_outcome_probabilities(circuit), TOTAL_QUBITS, num_system_qubits
        )
        for circuit in build_flagship_batch(d, TOTAL_QUBITS)
    }

    def win_rate(probe: str) -> float:
        correct_under_a = sum(
            probability
            for outcome, probability in outcomes[f"{probe}_I"].items()
            if outcome[0] == outcome[1]
        )
        correct_under_b = sum(
            probability
            for outcome, probability in outcomes[f"{probe}_V"].items()
            if outcome[0] != outcome[1]
        )
        return 0.5 * (correct_under_a + correct_under_b)

    assert win_rate("sep") == pytest.approx(SEPARABLE_SUCCESS, abs=1e-12)
    assert win_rate("me") == pytest.approx(simple_success(d), abs=1e-12)
    assert win_rate("me") == pytest.approx(1.0 - overlap(d) ** 2 / 2.0, abs=1e-12)
    assert win_rate("me") <= helstrom_ceiling(d) + 1e-12
    assert win_rate("me") < SEPARABLE_SUCCESS


def test_separable_circuits_are_deterministic() -> None:
    """One outcome with probability 1 each: no sampling noise in the ideal case."""
    for circuit in build_flagship_batch(FLAGGESHIP_D, TOTAL_QUBITS):
        if not circuit.name.startswith("sep"):
            continue
        probabilities = _exact_outcome_probabilities(circuit)
        assert len(probabilities) == 1
        assert next(iter(probabilities.values())) == pytest.approx(1.0, abs=1e-9)


def test_max_entangled_circuits_mix_over_many_outcomes() -> None:
    for channel in ("_I", "_V"):
        circuit = next(c for c in build_flagship_batch(16, 16) if c.name == f"me{channel}")
        assert len(_exact_outcome_probabilities(circuit)) > 1


# ------------------------------------------------------- result type guards


def test_circuit_spec_is_frozen_and_validated() -> None:
    spec = CircuitSpec(name="sep_I", probe_kind="SEPARABLE", channel="A")
    assert spec.name == "sep_I"
    with pytest.raises(Exception):
        spec.name = "other"
    with pytest.raises(ValueError):
        CircuitSpec(name="sep_I", probe_kind="PARTIAL", channel="A")
    with pytest.raises(ValueError):
        CircuitSpec(name="sep_I", probe_kind="SEPARABLE", channel="C")


def test_batch_result_rejects_an_unknown_circuit_name() -> None:
    result = run_batch(_FakeBackend(flagship_counts(shots=100)), shots=100)
    with pytest.raises(KeyError):
        result.counts_for("nope")
    assert result.counts_for("sep_I")
    assert result.probe_kind_for("me_V") == "MAX_ENTANGLEMENT"