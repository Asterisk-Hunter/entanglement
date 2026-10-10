"""Regression tests for the extensible `ChannelPair` API and the two verified pairs.

Task 2 scope: the fork interface, the HURTS flagship pair (identity vs `V`), the
HELPS pair (identity vs depolarizing), and the extension contract. Nothing here
branches on a specific pair slug except the loader tests themselves.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from channels.api import (  # noqa: E402
    BOUND_KINDS,
    PROBE_KINDS,
    ChannelPair,
    Strategy,
    available_pairs,
    load_pair,
    pair_payload,
)
from channels.helps_identity_depolarizing import (  # noqa: E402
    depolarizing_lambda,
    entangled_ceiling,
    separable_value,
)
from channels.hurts_identity_v import HURTS_PAIR  # noqa: E402
from quantum import science  # noqa: E402
from quantum.oracles import build_v_oracle, v_unitary_matrix  # noqa: E402

CLAIMS_PATH = REPO_ROOT / "claims.json"

HURTS_SLUG_EXPECTED = "hurts-identity-v"
HELPS_SLUG_EXPECTED = "helps-identity-depolarizing"
FOUR_PAULI_SLUG_EXPECTED = "comparator-four-pauli"
ALL_SLUGS = (HURTS_SLUG_EXPECTED, HELPS_SLUG_EXPECTED, FOUR_PAULI_SLUG_EXPECTED)

# Frozen HELPS fixtures from the verified Identity-vs-Depolarizing example.
HELPS_SEPARABLE = 0.75
HELPS_ENTANGLED = 0.875


def _safe_claims() -> list[dict]:
    data = json.loads(CLAIMS_PATH.read_text(encoding="utf-8"))
    return [claim for claim in data["claims"] if claim["safe_for_demo"]]


def _fidelity_of_operators(actual: np.ndarray, expected: np.ndarray) -> float:
    """Process fidelity between two unitaries; global-phase insensitive."""
    from qiskit.quantum_info import process_fidelity

    return float(process_fidelity(Operator(actual), Operator(expected)))


def _state_fidelity(actual: np.ndarray, expected: np.ndarray) -> float:
    """State fidelity |<expected|actual>|^2; global-phase insensitive."""
    return float(np.abs(np.vdot(expected, actual)) ** 2)


# ------------------------------------------------------- loader / interface


def test_load_pair_returns_hurts_pair() -> None:
    pair = load_pair(HURTS_SLUG_EXPECTED)
    assert isinstance(pair, ChannelPair)
    assert pair.slug == HURTS_SLUG_EXPECTED


def test_load_pair_returns_helps_pair() -> None:
    pair = load_pair(HELPS_SLUG_EXPECTED)
    assert isinstance(pair, ChannelPair)
    assert pair.slug == HELPS_SLUG_EXPECTED


def test_both_pairs_expose_one_common_interface() -> None:
    for slug in ALL_SLUGS:
        pair = load_pair(slug)
        assert isinstance(pair.name, str) and pair.name
        assert isinstance(pair.slug, str) and pair.slug == slug
        assert isinstance(pair.citation, str) and pair.citation
        assert isinstance(pair.dimension, int) and pair.dimension >= 2
        for method in ("build_a", "build_b", "strategies", "analytic_bounds"):
            assert callable(getattr(pair, method)), f"{slug} missing {method}"


def test_unknown_slug_raises_key_error() -> None:
    with pytest.raises(KeyError):
        load_pair("no-such-pair")
    with pytest.raises(KeyError):
        load_pair("hurts_identity_v")


def test_available_pairs_lists_exactly_the_registered_pairs() -> None:
    assert sorted(available_pairs()) == sorted(ALL_SLUGS)


def test_loader_returns_distinct_instances_of_the_same_type() -> None:
    first = load_pair(HURTS_SLUG_EXPECTED)
    second = load_pair(HURTS_SLUG_EXPECTED)
    assert type(first) is type(second)


# ---------------------------------------------------------- strategies()


@pytest.mark.parametrize(
    "slug", ALL_SLUGS, ids=str
)
def test_strategies_are_well_formed(slug: str) -> None:
    strategies = load_pair(slug).strategies()
    assert strategies
    slugs = [strategy.slug for strategy in strategies]
    assert len(slugs) == len(set(slugs))
    for strategy in strategies:
        assert isinstance(strategy, Strategy)
        assert isinstance(strategy.label, str) and strategy.label
        assert strategy.probe_kind in PROBE_KINDS
        assert strategy.bound_kind in BOUND_KINDS
        assert 0.0 <= strategy.analytic_value <= 1.0
        assert isinstance(strategy.claim_ids, tuple)


@pytest.mark.parametrize(
    "slug", ALL_SLUGS, ids=str
)
def test_both_pairs_offer_separable_and_max_entanglement(slug: str) -> None:
    probe_kinds = {strategy.probe_kind for strategy in load_pair(slug).strategies()}
    assert probe_kinds == set(PROBE_KINDS)


@pytest.mark.parametrize(
    "slug", ALL_SLUGS, ids=str
)
def test_strategy_claim_ids_resolve_to_safe_claims(slug: str) -> None:
    """Any cited claim must exist in claims.json and be safe_for_demo.

    `claims.json` currently carries only flagship claims, so the HELPS pair cites
    none. Empty citation is allowed; unsafe citation is not.
    """
    safe_ids = {claim["id"] for claim in _safe_claims()}
    for strategy in load_pair(slug).strategies():
        for claim_id in strategy.claim_ids:
            assert claim_id in safe_ids, f"{strategy.slug} cites unsafe claim {claim_id}"


def test_hurts_strategies_cite_the_flagship_claims() -> None:
    cited = {
        claim_id
        for strategy in load_pair(HURTS_SLUG_EXPECTED).strategies()
        for claim_id in strategy.claim_ids
    }
    assert cited == {
        "flagship_separable_d256",
        "flagship_simple_maxent_d256_formula",
    }


def test_depolarizing_strategies_cite_their_safe_claim_ledger_entries() -> None:
    cited = {
        claim_id
        for strategy in load_pair(HELPS_SLUG_EXPECTED).strategies()
        for claim_id in strategy.claim_ids
    }
    assert cited == {
        "helps_depolarizing_separable_d2",
        "helps_depolarizing_max_entangled_d2",
    }
    safe = {claim["id"] for claim in _safe_claims()}
    assert cited <= safe


def test_depolarizing_claims_are_listed_in_the_machine_readable_ledger() -> None:
    data = json.loads(CLAIMS_PATH.read_text(encoding="utf-8"))
    claims = {claim["id"]: claim for claim in data["claims"]}
    assert claims["helps_depolarizing_separable_d2"]["value"] == pytest.approx(0.75)
    assert claims["helps_depolarizing_max_entangled_d2"]["value"] == pytest.approx(0.875)


# --------------------------------------------------------- analytic_bounds()


def test_hurts_bounds_come_from_task1_formulas() -> None:
    """HURTS must call the Task 1 kernel, not restate its constants."""
    bounds = load_pair(HURTS_SLUG_EXPECTED).analytic_bounds()
    dimension = load_pair(HURTS_SLUG_EXPECTED).dimension
    assert bounds["separable"] == science.SEPARABLE_SUCCESS
    assert bounds["max_entanglement_simple"] == pytest.approx(
        science.simple_success(dimension), abs=1e-15
    )
    assert bounds["helstrom_ceiling"] == pytest.approx(
        science.helstrom_ceiling(dimension), abs=1e-15
    )
    assert bounds["overlap"] == pytest.approx(science.overlap(dimension), abs=1e-15)


def test_hurts_bounds_track_the_kernel_when_the_kernel_moves(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bounds are read from the kernel at call time, not frozen at import."""
    pair = load_pair(HURTS_SLUG_EXPECTED)
    monkeypatch.setattr(science, "simple_success", lambda d: 0.25)
    monkeypatch.setattr(science, "helstrom_ceiling", lambda d: 0.5)
    monkeypatch.setattr(science, "overlap", lambda d: -0.75)
    bounds = pair.analytic_bounds()
    assert bounds["max_entanglement_simple"] == 0.25
    assert bounds["helstrom_ceiling"] == 0.5
    assert bounds["overlap"] == -0.75


@pytest.mark.parametrize(
    "slug", ALL_SLUGS, ids=str
)
def test_analytic_bounds_schema_is_shared(slug: str) -> None:
    bounds = load_pair(slug).analytic_bounds()
    assert isinstance(bounds, dict)
    for key, value in bounds.items():
        assert isinstance(key, str) and key
        assert isinstance(value, float)
        # Every bound is a probability or a signed overlap, never outside [-1, 1].
        assert -1.0 <= value <= 1.0


def test_hurts_bounds_expose_the_three_required_keys() -> None:
    bounds = load_pair(HURTS_SLUG_EXPECTED).analytic_bounds()
    assert {"separable", "max_entanglement_simple", "helstrom_ceiling"} <= set(bounds)


def test_hurts_pair_is_the_registered_instance() -> None:
    assert load_pair(HURTS_SLUG_EXPECTED) is HURTS_PAIR
    assert HURTS_PAIR.dimension == 256
    assert HURTS_PAIR.slug == HURTS_SLUG_EXPECTED


def test_hurts_exposes_the_frozen_d256_values() -> None:
    bounds = load_pair(HURTS_SLUG_EXPECTED).analytic_bounds()
    assert bounds["separable"] == 1.0
    assert bounds["overlap"] == -0.9921875
    assert bounds["helstrom_ceiling"] == pytest.approx(
        0.5623778102448098, abs=1e-15
    )


def test_no_pair_bound_surfaces_the_superseded_printed_figure() -> None:
    """The printed d=256 simple figure is safe_for_demo=false and must not leak."""
    printed = 0.5078125
    for slug in ALL_SLUGS:
        for key, value in load_pair(slug).analytic_bounds().items():
            assert abs(value - printed) > 1e-9, f"{slug}/{key} exposes {printed}"
        for strategy in load_pair(slug).strategies():
            assert abs(strategy.analytic_value - printed) > 1e-9, (
                f"{slug}/{strategy.slug} exposes {printed}"
            )


# ------------------------------------------------------------ build_a / build_b


@pytest.mark.parametrize(
    "slug", ALL_SLUGS, ids=str
)
def test_build_methods_return_padded_circuits(slug: str) -> None:
    pair = load_pair(slug)
    num_system_qubits = pair.dimension.bit_length() - 1
    total_qubits = 16
    for method in ("build_a", "build_b"):
        circuit = getattr(pair, method)(num_system_qubits, total_qubits)
        assert isinstance(circuit, QuantumCircuit)
        assert circuit.num_qubits == total_qubits, f"{slug}.{method} width"


@pytest.mark.parametrize(
    "slug", ALL_SLUGS, ids=str
)
def test_build_methods_reject_total_below_system_width(slug: str) -> None:
    pair = load_pair(slug)
    num_system_qubits = pair.dimension.bit_length() - 1
    with pytest.raises(ValueError):
        pair.build_a(num_system_qubits, num_system_qubits - 1)
    with pytest.raises(ValueError):
        pair.build_b(num_system_qubits, num_system_qubits - 1)


def test_hurts_build_a_is_the_identity_channel() -> None:
    pair = load_pair(HURTS_SLUG_EXPECTED)
    circuit = pair.build_a(4, 8)
    assert list(circuit.data) == [], "identity channel must contain no operations"
    assert np.allclose(Operator(circuit).data, np.eye(2**8), atol=1e-12)


def test_hurts_build_b_is_the_v_oracle_up_to_global_phase() -> None:
    """Same channel as the shared Task 1 builder: process fidelity, not phases."""
    pair = load_pair(HURTS_SLUG_EXPECTED)
    num_system_qubits, total_qubits = 3, 5
    built = Operator(pair.build_b(num_system_qubits, total_qubits)).data
    reference = Operator(build_v_oracle(num_system_qubits, total_qubits)).data
    assert _fidelity_of_operators(built, reference) == pytest.approx(1.0, abs=1e-12)
    assert np.allclose(np.abs(built), np.abs(reference), atol=1e-12)


def test_hurts_build_b_matches_definition_matrix_up_to_phase() -> None:
    """On the system register, `V` is diag(+1, -1, ..., -1) up to global phase."""
    pair = load_pair(HURTS_SLUG_EXPECTED)
    num_system_qubits, total_qubits = 3, 3
    built = Operator(pair.build_b(num_system_qubits, total_qubits)).data
    expected = v_unitary_matrix(num_system_qubits)
    phase = built[0, 0] / expected[0, 0]
    assert abs(abs(phase) - 1.0) < 1e-12
    assert np.allclose(built, phase * expected, atol=1e-12)


def test_hurts_build_b_matches_definition_fidelity_only() -> None:
    """`V|0...0> = +|0...0>` and `V|x> = -|x>` compared by fidelity."""
    pair = load_pair(HURTS_SLUG_EXPECTED)
    num_system_qubits = 4
    unitary = Operator(pair.build_b(num_system_qubits, num_system_qubits)).data
    size = 2**num_system_qubits
    for index in range(size):
        prepared = np.zeros(size, dtype=complex)
        prepared[index] = 1.0
        result = unitary @ prepared
        expected = prepared if index == 0 else -prepared
        assert _state_fidelity(result, expected) == pytest.approx(1.0, abs=1e-12)


def test_hurts_build_b_leaves_padding_idle() -> None:
    pair = load_pair(HURTS_SLUG_EXPECTED)
    circuit = pair.build_b(4, 8)
    touched = {
        circuit.find_bit(qubit).index
        for instruction in circuit.data
        for qubit in instruction.qubits
    }
    assert touched == set(range(4))


def test_helps_build_b_carries_one_qubit_channel_instruction() -> None:
    pair = load_pair(HELPS_SLUG_EXPECTED)
    circuit = pair.build_b(1, 4)
    assert circuit.num_qubits == 4
    assert len(circuit.data) == 1
    operation = circuit.data[0].operation
    assert operation.num_qubits == 1
    assert circuit.data[0].qubits == (circuit.qubits[0],)


def test_helps_build_b_channel_is_the_declared_depolarizing_channel() -> None:
    """The appended instruction equals `depolarizing_error(lambda, 1)` exactly."""
    from qiskit_aer.noise import depolarizing_error

    pair = load_pair(HELPS_SLUG_EXPECTED)
    circuit = pair.build_b(1, 4)
    operation = circuit.data[0].operation
    reference = depolarizing_error(depolarizing_lambda(), 1).to_instruction()
    assert operation == reference
    assert operation.soft_compare(reference)


def test_helps_build_b_channel_sends_every_register_state_to_i_over_2() -> None:
    """At lambda = 1 the channel replaces the register state by I/2.

    Read from the superoperator of the depolarizing error itself, since the
    circuit instruction wrapper exposes no channel matrix. Full depolarization
    is `E(X) = Tr(X) * I/2`, so basis matrices of nonzero trace map to `I/2` and
    traceless ones map to zero.
    """
    from qiskit.quantum_info import SuperOp
    from qiskit_aer.noise import depolarizing_error

    lam = depolarizing_lambda()
    superop = np.asarray(SuperOp(depolarizing_error(lam, 1).to_quantumchannel()).data)
    mixed_in_vektor = np.array([0.5, 0.0, 0.0, 0.5])  # vec(I/2), column-stacked
    for basis_index, trace in ((0, 1.0), (3, 1.0), (1, 0.0), (2, 0.0)):
        assert np.allclose(
            superop[:, basis_index], trace * mixed_in_vektor, atol=1e-12
        ), f"basis matrix index {basis_index}"


def test_helps_build_b_preserves_the_maximally_mixed_register() -> None:
    """Trace preservation on the register the channel acts on."""
    from qiskit.quantum_info import DensityMatrix
    from qiskit_aer.noise import depolarizing_error

    channel = depolarizing_error(depolarizing_lambda(), 1).to_quantumchannel()
    output = DensityMatrix(np.eye(2) / 2).evolve(channel).data
    assert np.allclose(output, np.eye(2) / 2, atol=1e-12)


def test_helps_build_a_is_identity() -> None:
    pair = load_pair(HELPS_SLUG_EXPECTED)
    circuit = pair.build_a(1, 4)
    assert list(circuit.data) == []
    assert np.allclose(Operator(circuit).data, np.eye(2**4), atol=1e-12)


# ------------------------------------------- HELPS trace-norm derivation


def test_helps_separable_fixture_matches_trace_norm_derivation() -> None:
    """Separable probe optimum from ||rho_I - rho_D||_1, not a literal constant."""
    lam = depolarizing_lambda()
    # Separable probe |0><0|_A (x) I/2_B, depolarizing applied to B.
    basis = np.array([1.0, 0.0])
    rho_under_a = np.outer(basis, basis)
    identity_term = np.outer(basis, basis)
    depolarized_term = lam * np.eye(2) / 2 + (1 - lam) * np.outer(basis, basis)
    delta = identity_term - depolarized_term
    trace_norm = float(np.abs(np.linalg.eigvalsh(delta)).sum())
    derived = 0.5 + 0.25 * trace_norm
    assert derived == pytest.approx(HELPS_SEPARABLE, abs=1e-12)
    assert separable_value() == pytest.approx(derived, abs=1e-12)
    assert rho_under_a.shape == (2, 2)  # probe factor carried explicitly


def test_helps_entangled_fixture_matches_trace_norm_derivation() -> None:
    """Bell probe: 4x4 difference of the two channel outputs, Helstrom from it."""
    lam = depolarizing_lambda()
    bell = np.array([1.0, 0.0, 0.0, 1.0]) / np.sqrt(2.0)
    phi = np.outer(bell, bell.conj())
    identity_output = phi
    depolarized_output = lam * np.eye(4) / 4 + (1 - lam) * phi
    delta = identity_output - depolarized_output
    eigenvalues = np.linalg.eigvalsh(delta)
    trace_norm = float(np.abs(eigenvalues).sum())
    derived = 0.5 + 0.25 * trace_norm
    assert derived == pytest.approx(HELPS_ENTANGLED, abs=1e-12)
    assert entangled_ceiling() == pytest.approx(derived, abs=1e-12)
    # `eigvalsh` returns ascending order: the Bell state is the +3/4 eigenvalue,
    # the orthogonal complement carries -1/4 three times.
    assert eigenvalues[-1] == pytest.approx(0.75, abs=1e-12)
    assert np.allclose(eigenvalues[:-1], -0.25, atol=1e-12)
    assert trace_norm == pytest.approx(1.5, abs=1e-12)


def test_helps_analytic_bounds_match_frozen_fixtures() -> None:
    bounds = load_pair(HELPS_SLUG_EXPECTED).analytic_bounds()
    assert bounds["separable"] == pytest.approx(HELPS_SEPARABLE, abs=1e-12)
    assert bounds["max_entanglement_simple"] == pytest.approx(
        HELPS_ENTANGLED, abs=1e-12
    )


def test_helps_entanglement_helps() -> None:
    bounds = load_pair(HELPS_SLUG_EXPECTED).analytic_bounds()
    assert bounds["max_entanglement_simple"] > bounds["separable"]


def test_hurts_entanglement_hurts() -> None:
    bounds = load_pair(HURTS_SLUG_EXPECTED).analytic_bounds()
    assert bounds["max_entanglement_simple"] < bounds["separable"]


# ------------------------------------------------------- payload / no branching


@pytest.mark.parametrize(
    "slug", ALL_SLUGS, ids=str
)
def test_pair_payload_schema_is_identical_across_pairs(slug: str) -> None:
    payload = pair_payload(load_pair(slug))
    assert set(payload) == {
        "name",
        "slug",
        "citation",
        "dimension",
        "strategies",
        "bounds",
    }
    assert isinstance(payload["strategies"], list)
    for entry in payload["strategies"]:
        assert set(entry) == {
            "slug",
            "label",
            "probe_kind",
            "bound_kind",
            "analytic_value",
            "claim_ids",
        }
    # Must survive JSON serialization unchanged: no Python proxy types.
    assert json.loads(json.dumps(payload)) == payload


@pytest.mark.parametrize(
    "slug", ALL_SLUGS, ids=str
)
def test_payload_never_marks_anything_empirical(slug: str) -> None:
    """Everything exposed here is analytic or a ceiling, never a measurement."""
    payload = pair_payload(load_pair(slug))
    for entry in payload["strategies"]:
        assert entry["bound_kind"] in {"ANALYTIC", "THEORETICAL_CEILING"}


# ------------------------------------------------------ extension contract


class _SyntheticPair(ChannelPair):
    """Third pair declared only inside this test module."""

    name = "Synthetic Test Pair"
    slug = "synthetic-test-pair"
    citation = "local test fixture, no external claim"
    dimension = 2

    def build_a(self, num_system_qubits: int, total_qubits: int) -> QuantumCircuit:
        if total_qubits < num_system_qubits:
            raise ValueError("total_qubits must cover the system register")
        return QuantumCircuit(total_qubits, name="synthetic_a")

    def build_b(self, num_system_qubits: int, total_qubits: int) -> QuantumCircuit:
        if total_qubits < num_system_qubits:
            raise ValueError("total_qubits must cover the system register")
        circuit = QuantumCircuit(total_qubits, name="synthetic_b")
        circuit.x(0)
        return circuit

    def strategies(self) -> tuple[Strategy, ...]:
        return (
            Strategy(
                slug="synthetic-separable",
                label="SYNTHETIC",
                probe_kind="SEPARABLE",
                bound_kind="ANALYTIC",
                analytic_value=1.0,
                claim_ids=(),
            ),
        )

    def analytic_bounds(self) -> dict[str, float]:
        return {"separable": 1.0}


def test_synthetic_pair_needs_no_loader_consumer_change() -> None:
    """The same consumer helpers must accept an unknown third pair unchanged."""
    synthetic = _SyntheticPair()
    payload = pair_payload(synthetic)
    assert payload["slug"] == "synthetic-test-pair"
    assert json.loads(json.dumps(payload)) == payload
    circuit = synthetic.build_a(1, 4)
    assert circuit.num_qubits == 4
    assert synthetic.build_b(1, 4).num_qubits == 4
    assert synthetic.strategies()[0].probe_kind in PROBE_KINDS
    assert set(synthetic.analytic_bounds()) == {"separable"}


def test_synthetic_pair_is_not_in_the_registry() -> None:
    assert "synthetic-test-pair" not in available_pairs()
    with pytest.raises(KeyError):
        load_pair("synthetic-test-pair")


def test_channel_pair_cannot_be_instantiated_incomplete() -> None:
    with pytest.raises(TypeError):
        ChannelPair()  # type: ignore[abstract]


@pytest.mark.parametrize(
    "slug", ALL_SLUGS, ids=str
)
def test_pair_citations_are_not_empty_placeholders(slug: str) -> None:
    citation = load_pair(slug).citation
    assert "TODO" not in citation
    assert "tbd" not in citation.lower()
    assert len(citation) > 10


# ------------------------------------------------------------ novelty guard


def _phrase_positions(text: str, phrase: str):
    start = 0
    while True:
        index = text.find(phrase, start)
        if index < 0:
            return
        yield index
        start = index + len(phrase)


def _negated(prefix: str) -> bool:
    return any(
        prefix.rstrip().endswith(word)
        for word in ("no", "not", "never", "neither", "nor")
    )


FORBIDDEN_NOVELTY_PHRASES = (
    "we discovered",
    "we have discovered",
    "quantum advantage",
    "quantum computational advantage",
    "breakthrough",
    "first time",
    "new theorem",
)


@pytest.mark.parametrize(
    "module",
    [
        "channels/__init__.py",
        "channels/api.py",
        "channels/hurts_identity_v.py",
        "channels/helps_identity_depolarizing.py",
    ],
    ids=str,
)
def test_channel_modules_avoid_novelty_language(module: str) -> None:
    """No discovery-of-theorem or quantum-advantage wording, comments included."""
    text = (REPO_ROOT / module).read_text(encoding="utf-8").lower()
    for phrase in FORBIDDEN_NOVELTY_PHRASES:
        for index in _phrase_positions(text, phrase):
            prefix = text[max(0, index - 12) : index]
            assert _negated(prefix), f"{module} contains {phrase!r} (prefix {prefix!r})"


@pytest.mark.parametrize(
    "slug", ALL_SLUGS, ids=str
)
def test_pair_names_and_labels_are_not_novelty_copy(slug: str) -> None:
    pair = load_pair(slug)
    surfaced = [pair.name, pair.citation] + [
        strategy.label for strategy in pair.strategies()
    ]
    for text in surfaced:
        lowered = text.lower()
        for phrase in FORBIDDEN_NOVELTY_PHRASES:
            assert phrase not in lowered, f"{slug} exposes {phrase!r} in {text!r}"
