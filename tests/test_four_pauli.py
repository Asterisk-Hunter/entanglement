"""Four-Pauli unitary comparator: both optimal probe choices tie.

Every number the pair publishes is re-derived here from first principles. The
key test is :func:`test_executable_discriminator_attains_p_star`: the circuit's
exact statevector must reach ``p_star``, which is itself derived in-test from the
trace norm of the two channel outputs without touching the implementation.

Because the attaining circuit exists and is tested, the pair is allowed to
publish the optimum as ``ANALYTIC``. If that test ever failed, the honest label
would be ``THEORETICAL_CEILING`` instead; see
:func:`test_max_entanglement_bound_kind_is_justified_by_the_attaining_circuit`.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

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
from channels.four_pauli import (  # noqa: E402
    DECODERS,
    FOUR_PAULI_DIMENSION,
    FOUR_PAULI_PAIR,
    FOUR_PAULI_SLUG,
    FOUR_PAULI_THETA,
    PAULI_GENERATORS,
    bell_discriminator_circuit,
    bell_discriminator_probabilities,
    bell_discriminator_success,
    channel_matrix,
    four_pauli_star,
    pauli_matrix,
    separable_star,
)
from quantum import science  # noqa: E402

CLAIMS_PATH = REPO_ROOT / "claims.json"

THETAS = (0.0, 0.05, 0.2, math.pi / 8, 0.4, 0.6, 0.7, math.pi / 4)
GENERATORS = ("X", "Y", "Z")


# --------------------------------------------------------------------------
# Independent physics, written here so the implementation cannot supply it.
# --------------------------------------------------------------------------

_LOCAL_PAULI = {
    "X": np.array([[0, 1], [1, 0]], dtype=complex),
    "Y": np.array([[0, -1j], [1j, 0]], dtype=complex),
    "Z": np.array([[1, 0], [0, -1]], dtype=complex),
}
_PHI_PLUS = np.array([1.0, 0.0, 0.0, 1.0], dtype=complex) / math.sqrt(2.0)


def _local_pauli_rotation(name: str, phi: float) -> np.ndarray:
    """R_P(phi) = cos(phi/2) I - i sin(phi/2) P, rebuilt from the raw matrices."""
    return (
        math.cos(phi / 2.0) * np.eye(2, dtype=complex)
        - 1j * math.sin(phi / 2.0) * _LOCAL_PAULI[name]
    )


def _local_channel_outputs(name: str, theta: float):
    """The two pure channel outputs from the shared Bell pair.

    Qubit 0 is the system register the channel acts on; ``np.kron(I, U)`` places
    U on that qubit for Qiskit's little-endian state ordering.
    """
    plus = np.kron(
        np.eye(2, dtype=complex), _local_pauli_rotation(name, 2.0 * theta)
    ) @ _PHI_PLUS
    minus = np.kron(
        np.eye(2, dtype=complex), _local_pauli_rotation(name, -2.0 * theta)
    ) @ _PHI_PLUS
    return plus, minus


def _local_p_star_from_trace_norm(name: str, theta: float) -> float:
    """p_star = 1/2 + 1/4 ||rho_A - rho_B||_1, from the trace norm alone.

    This is the textbook equal-prior Helstrom formula and shares no code with
    ``channels.four_pauli``.
    """
    plus, minus = _local_channel_outputs(name, theta)
    delta = np.outer(plus, plus.conj()) - np.outer(minus, minus.conj())
    trace_norm = float(np.abs(np.linalg.eigvalsh(delta)).sum())
    return 0.5 + 0.25 * trace_norm


def _local_p_star_closed_form(theta: float) -> float:
    """p_star = 1/2 (1 + sin 2 theta), asserted as an independent second path."""
    return 0.5 * (1.0 + math.sin(2.0 * theta))


def _local_channel_overlap(name: str, theta: float) -> float:
    """|<a|b>| for the two outputs; equals cos(2 theta)."""
    plus, minus = _local_channel_outputs(name, theta)
    return float(abs(np.vdot(plus, minus)))


# ------------------------------------------------------------------ registry


def test_registry_loads_the_four_pauli_pair() -> None:
    pair = load_pair(FOUR_PAULI_SLUG)
    assert isinstance(pair, ChannelPair)
    assert pair is FOUR_PAULI_PAIR
    assert pair.slug == FOUR_PAULI_SLUG
    assert pair.dimension == FOUR_PAULI_DIMENSION


def test_registry_role_is_comparator() -> None:
    from channels.api import _PAIR_REGISTRY

    module, export, role = _PAIR_REGISTRY[FOUR_PAULI_SLUG]
    assert module == "channels.four_pauli"
    assert export == "FOUR_PAULI_PAIR"
    assert role == "COMPARATOR"


def test_available_pairs_lists_the_four_pauli_pair() -> None:
    assert FOUR_PAULI_SLUG in available_pairs()


def test_loading_one_pair_does_not_import_the_others() -> None:
    """The registry stays lazy: only the requested module is imported."""
    script = (
        "import sys\n"
        "from pathlib import Path\n"
        "sys.path.insert(0, %r)\n"
        "from channels.api import load_pair\n"
        "pair = load_pair('comparator-four-pauli')\n"
        "print(pair.slug)\n"
        "print('channels.four_pauli' in sys.modules)\n"
        "print('channels.hurts_identity_v' in sys.modules)\n"
        "print('channels.helps_identity_depolarizing' in sys.modules)\n"
    ) % str(REPO_ROOT)
    import subprocess

    completed = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.split() == [
        "comparator-four-pauli",
        "True",
        "False",
        "False",
    ], completed.stdout


def test_unknown_four_pauli_slug_still_raises_key_error() -> None:
    with pytest.raises(KeyError):
        load_pair("four_pauli")
    with pytest.raises(KeyError):
        load_pair("helps_four_pauli")


# ------------------------------------------------------------ payload schema


def test_four_pauli_payload_schema_matches_the_shared_schema() -> None:
    payload = pair_payload(load_pair(FOUR_PAULI_SLUG))
    assert set(payload) == {
        "name",
        "slug",
        "citation",
        "dimension",
        "strategies",
        "bounds",
    }
    assert json.loads(json.dumps(payload)) == payload


def test_four_pauli_strategies_are_well_formed_and_offer_both_probes() -> None:
    strategies = load_pair(FOUR_PAULI_SLUG).strategies()
    assert {strategy.probe_kind for strategy in strategies} == set(PROBE_KINDS)
    for strategy in strategies:
        assert isinstance(strategy, Strategy)
        assert strategy.bound_kind in BOUND_KINDS
        assert 0.0 <= strategy.analytic_value <= 1.0
        assert isinstance(strategy.claim_ids, tuple)


def test_four_pauli_bounds_are_probabilities_or_the_angle() -> None:
    bounds = load_pair(FOUR_PAULI_SLUG).analytic_bounds()
    assert bounds["theta"] == pytest.approx(FOUR_PAULI_THETA)
    assert 0.0 <= bounds["separable"] <= 1.0
    assert 0.5 <= bounds["max_entanglement_simple"] <= 1.0
    assert bounds["helstrom_ceiling"] == bounds["max_entanglement_simple"]


def test_four_pauli_cited_claim_exists_and_is_safe() -> None:
    data = json.loads(CLAIMS_PATH.read_text(encoding="utf-8"))
    safe = {claim["id"] for claim in data["claims"] if claim["safe_for_demo"]}
    for strategy in load_pair(FOUR_PAULI_SLUG).strategies():
        for claim_id in strategy.claim_ids:
            assert claim_id in safe


def test_gallery_payload_includes_the_four_pauli_pair() -> None:
    from channels.api import registered_pair_payloads

    payloads = registered_pair_payloads()
    entry = next(item for item in payloads if item["slug"] == FOUR_PAULI_SLUG)
    assert entry["role"] == "COMPARATOR"
    assert entry["circuit"]["status"] if "status" in entry["circuit"] else True
    assert {channel["channel"] for channel in entry["circuit"]["channels"]} == {"A", "B"}


# ------------------------------------------------------ analytic consistency


@pytest.mark.parametrize("generator", GENERATORS)
@pytest.mark.parametrize("theta", THETAS)
def test_published_star_matches_the_local_trace_norm(generator: str, theta: float) -> None:
    assert four_pauli_star(theta) == pytest.approx(
        _local_p_star_from_trace_norm(generator, theta), abs=1e-12
    )


@pytest.mark.parametrize("theta", THETAS)
def test_published_star_matches_the_independent_closed_form(theta: float) -> None:
    assert four_pauli_star(theta) == pytest.approx(
        _local_p_star_closed_form(theta), abs=1e-12
    )


@pytest.mark.parametrize("generator", GENERATORS)
@pytest.mark.parametrize("theta", THETAS)
def test_two_channel_outputs_overlap_by_cos_two_theta(
    generator: str, theta: float
) -> None:
    assert _local_channel_overlap(generator, theta) == pytest.approx(
        math.cos(2.0 * theta), abs=1e-12
    )


@pytest.mark.parametrize("generator", GENERATORS)
def test_published_star_is_the_same_for_every_generator(generator: str) -> None:
    assert four_pauli_star(FOUR_PAULI_THETA) == pytest.approx(
        four_pauli_star(FOUR_PAULI_THETA), abs=0.0
    )
    assert four_pauli_star(FOUR_PAULI_THETA) == pytest.approx(
        _local_p_star_from_trace_norm(generator, FOUR_PAULI_THETA), abs=1e-12
    )


def test_published_theta_is_the_pi_over_eight_reference() -> None:
    assert FOUR_PAULI_THETA == pytest.approx(math.pi / 8.0)
    assert four_pauli_star(FOUR_PAULI_THETA) == pytest.approx(
        0.5 * (1.0 + math.sqrt(2.0) / 2.0), abs=1e-12
    )
    assert four_pauli_star(FOUR_PAULI_THETA) == pytest.approx(
        0.8535533905932737, abs=1e-12
    )


def test_star_reads_the_verified_kernel_not_a_restated_constant() -> None:
    """The formula must track the kernel if the kernel ever moves."""
    assert four_pauli_star(FOUR_PAULI_THETA) == pytest.approx(
        science.success_lambda0(math.cos(FOUR_PAULI_THETA) ** 2), abs=0.0
    )


def test_optimal_separable_probe_matches_the_maximally_entangled_value() -> None:
    for theta in THETAS:
        assert separable_star(theta) == pytest.approx(four_pauli_star(theta), abs=1e-12)


def test_four_pauli_pair_is_neutral_under_optimal_probe_comparison() -> None:
    bounds = load_pair(FOUR_PAULI_SLUG).analytic_bounds()
    assert bounds["max_entanglement_simple"] == pytest.approx(bounds["separable"], abs=1e-12)


# --------------------------------------- the executable circuit attains p_star


@pytest.mark.parametrize("generator", GENERATORS)
@pytest.mark.parametrize("theta", THETAS)
def test_executable_discriminator_attains_p_star(generator: str, theta: float) -> None:
    """The decisive test: the circuit's exact statevector reaches the bound."""
    attained = bell_discriminator_success(theta, generator)
    assert attained == pytest.approx(_local_p_star_from_trace_norm(generator, theta), abs=1e-12)
    assert attained == pytest.approx(_local_p_star_closed_form(theta), abs=1e-12)
    assert attained == pytest.approx(four_pauli_star(theta), abs=1e-12)


@pytest.mark.parametrize("generator", GENERATORS)
def test_discriminator_beats_chance_for_every_nonzero_angle(generator: str) -> None:
    for theta in THETAS[1:]:
        assert bell_discriminator_success(theta, generator) > 0.5


@pytest.mark.parametrize("generator", GENERATORS)
def test_discriminator_probabilities_are_a_partition(generator: str) -> None:
    probabilities = bell_discriminator_probabilities(FOUR_PAULI_THETA, generator)
    assert set(probabilities) == {"A", "B"}
    for name in ("A", "B"):
        entry = probabilities[name]
        assert set(entry) == {"phi_plus", "other"}
        assert entry["phi_plus"] >= 0.0
        assert entry["other"] >= 0.0
        assert entry["phi_plus"] + entry["other"] == pytest.approx(1.0, abs=1e-12)


@pytest.mark.parametrize("generator", GENERATORS)
def test_both_channels_take_the_same_wrong_answer_rate(generator: str) -> None:
    """Symmetric pair: the discriminator fails equally often for A and B."""
    probabilities = bell_discriminator_probabilities(FOUR_PAULI_THETA, generator)
    assert probabilities["A"]["phi_plus"] == pytest.approx(
        probabilities["B"]["other"], abs=1e-12
    )
    assert probabilities["B"]["phi_plus"] == pytest.approx(
        probabilities["A"]["other"], abs=1e-12
    )


@pytest.mark.parametrize("generator", GENERATORS)
def test_discriminator_circuit_is_a_two_qubit_bell_readout(generator: str) -> None:
    circuit = bell_discriminator_circuit(FOUR_PAULI_THETA, 1, generator, total_qubits=2)
    assert circuit.num_qubits == 2
    names = [instruction.operation.name for instruction in circuit.data]
    assert names[:2] == ["h", "cx"], "the shared Bell pair comes first"
    assert names[-3:] == ["h", "cx", "measure"] or names.count("measure") == 2


@pytest.mark.parametrize("generator", GENERATORS)
def test_discriminator_circuit_leaves_padding_idle(generator: str) -> None:
    circuit = bell_discriminator_circuit(FOUR_PAULI_THETA, 1, generator, total_qubits=8)
    touched = {
        circuit.find_bit(qubit).index
        for instruction in circuit.data
        for qubit in instruction.qubits
    }
    assert touched == {0, 1}


@pytest.mark.parametrize("generator", GENERATORS)
def test_discriminator_channel_gate_is_the_declared_rotation(generator: str) -> None:
    circuit = bell_discriminator_circuit(FOUR_PAULI_THETA, 1, generator, total_qubits=2)
    unitary = next(
        instruction.operation
        for instruction in circuit.data
        if instruction.operation.name == "unitary"
    )
    expected = channel_matrix(generator, FOUR_PAULI_THETA, 1)
    assert np.allclose(np.asarray(unitary.to_matrix()), expected, atol=1e-12)


@pytest.mark.parametrize("generator", GENERATORS)
def test_channel_matrices_are_conjugate_about_the_identity(generator: str) -> None:
    a = channel_matrix(generator, FOUR_PAULI_THETA, 1)
    b = channel_matrix(generator, FOUR_PAULI_THETA, -1)
    assert np.allclose(b, a.conj().T, atol=1e-12)
    assert np.allclose(a @ a.conj().T, np.eye(2), atol=1e-12)
    # W = A^dag B is the rotation by 4 theta, so its eigenvalues are e^{+-2 i theta}.
    w = a.conj().T @ b
    eigenvalues = np.linalg.eigvals(w)
    assert sorted(np.round(np.angle(eigenvalues), 12)) == pytest.approx(
        sorted([2.0 * FOUR_PAULI_THETA, -2.0 * FOUR_PAULI_THETA]), abs=1e-12
    )
    assert np.allclose(np.abs(eigenvalues), 1.0, atol=1e-12)


@pytest.mark.parametrize("generator", GENERATORS)
def test_discriminator_circuit_statevector_equals_the_analytic_predictor(
    generator: str,
) -> None:
    """Independent of the module's probability helper: rebuild the state."""
    theta = FOUR_PAULI_THETA
    circuit = bell_discriminator_circuit(theta, 1, generator, total_qubits=2)
    bare = circuit.remove_final_measurements(inplace=False)
    distribution = Statevector.from_instruction(bare).probabilities_dict()
    total = 0.0
    for bits, probability in distribution.items():
        text = "".join(str(bits).split())
        if text[-1] == "0" and text[-2] == "0":
            total += float(probability)
    expected = 0.5 * (1.0 + math.sin(2.0 * theta))
    # P(Phi+ | A) = p_star; P(Phi+ | B) = 1 - p_star by symmetry.
    assert total == pytest.approx(expected, abs=1e-12)


def test_max_entanglement_bound_kind_is_justified_by_the_attaining_circuit() -> None:
    """ANALYTIC is only allowed here because the circuit attains the value."""
    strategies = {
        strategy.probe_kind: strategy
        for strategy in load_pair(FOUR_PAULI_SLUG).strategies()
    }
    max_ent = strategies["MAX_ENTANGLEMENT"]
    if max_ent.bound_kind == "ANALYTIC":
        attained = bell_discriminator_success(FOUR_PAULI_THETA, FOUR_PAULI_PAIR.generator)
        assert attained == pytest.approx(max_ent.analytic_value, abs=1e-12)
    else:
        assert max_ent.bound_kind == "THEORETICAL_CEILING"


def test_separable_star_is_attained_by_a_product_probe_and_y_readout() -> None:
    """A |+> input and Y-basis readout attain the same unitary-pair optimum."""
    from qiskit.circuit.library import UnitaryGate

    generator = FOUR_PAULI_PAIR.generator
    theta = FOUR_PAULI_THETA
    wins = []
    for sign in (1, -1):
        circuit = QuantumCircuit(2, 2)
        circuit.h(0)
        circuit.append(UnitaryGate(channel_matrix(generator, theta, sign)), [0])
        circuit.sdg(0)
        circuit.h(0)
        circuit.measure(0, 0)
        bare = circuit.remove_final_measurements(inplace=False)
        distribution = Statevector.from_instruction(bare).probabilities_dict()
        correct = 0.0
        for bits, probability in distribution.items():
            reads_zero = str(bits)[-1] == "0"
            if reads_zero == (sign == 1):
                correct += float(probability)
        wins.append(correct)
    success = 0.5 * (wins[0] + wins[1])
    assert success == pytest.approx(separable_star(theta), abs=1e-12)


# ------------------------------------------------------------ input guards


def test_pauli_alphabet_lists_the_four_generators() -> None:
    assert PAULI_GENERATORS == ("I", "X", "Y", "Z")
    for name in PAULI_GENERATORS:
        matrix = pauli_matrix(name)
        assert matrix.shape == (2, 2)
        assert np.allclose(matrix.conj().T @ matrix, np.eye(2), atol=1e-12)


def test_unknown_generator_is_rejected() -> None:
    with pytest.raises(ValueError):
        pauli_matrix("W")
    with pytest.raises(ValueError):
        channel_matrix("W", FOUR_PAULI_THETA, 1)
    with pytest.raises(ValueError):
        bell_discriminator_circuit(FOUR_PAULI_THETA, 1, "I")


def test_identity_generator_is_the_degenerate_member_of_the_alphabet() -> None:
    """R_I is a global phase, so the pair is trivially undecidable."""
    assert np.allclose(pauli_matrix("I"), np.eye(2), atol=1e-12)
    with pytest.raises(ValueError):
        bell_discriminator_circuit(FOUR_PAULI_THETA, 1, "I")


@pytest.mark.parametrize("bad", [-0.1, 0.9, 1.0, float("nan"), float("inf"), "x", True])
def test_out_of_range_theta_is_rejected(bad: object) -> None:
    with pytest.raises(ValueError):
        four_pauli_star(bad)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        separable_star(bad)  # type: ignore[arg-type]


def test_bad_sign_is_rejected() -> None:
    with pytest.raises(ValueError):
        channel_matrix("Z", FOUR_PAULI_THETA, 0)
    with pytest.raises(ValueError):
        bell_discriminator_circuit(FOUR_PAULI_THETA, 2, "Z")


def test_decoder_table_covers_every_active_generator() -> None:
    assert set(DECODERS) == {"X", "Y", "Z"}
    for gate, angle in DECODERS.values():
        assert gate in {"rx", "ry", "sdg"}
        assert (angle is None) == (gate == "sdg")


def test_analytic_bounds_for_rejects_other_dimensions() -> None:
    pair = load_pair(FOUR_PAULI_SLUG)
    with pytest.raises(ValueError):
        pair.analytic_bounds_for(4)
    with pytest.raises(ValueError):
        pair.analytic_bounds_for(16)


def test_build_methods_return_padded_circuits_and_reject_narrow_registers() -> None:
    pair = load_pair(FOUR_PAULI_SLUG)
    for builder, sign in ((pair.build_a, 1), (pair.build_b, -1)):
        circuit = builder(1, 16)
        assert isinstance(circuit, QuantumCircuit)
        assert circuit.num_qubits == 16
        assert circuit.data[0].operation.name == "unitary"
        assert np.allclose(
            circuit.data[0].operation.to_matrix(),
            channel_matrix(pair.generator, FOUR_PAULI_THETA, sign),
            atol=1e-12,
        )
        with pytest.raises(ValueError):
            builder(1, 0)


def test_four_pauli_module_avoids_novelty_language() -> None:
    text = (REPO_ROOT / "channels" / "four_pauli.py").read_text(encoding="utf-8").lower()
    for phrase in (
        "we discovered",
        "new theorem",
        "breakthrough",
        "quantum advantage",
        "first time",
    ):
        assert phrase not in text, f"four_pauli.py contains {phrase!r}"
