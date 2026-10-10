"""Regression tests for the channel-discrimination science kernel.

Scope: analytic formulas, frozen claim fixtures, and the `V` oracle action.
All values in `GOLDEN_*` tables are ANALYTIC values derived from the design
verified formulas, except where a historical printed value is recorded separately.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest
from qiskit import QuantumCircuit

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from quantum.oracles import (  # noqa: E402
    build_v_oracle,
    v_unitary_matrix,
)
from quantum.science import (  # noqa: E402
    GOLDEN_DIMENSIONS,
    SCIPY_AVAILABLE,
    SEPARABLE_SUCCESS,
    centroid_and_hull,
    helstrom_ceiling,
    maxent_lambda0,
    overlap,
    simple_success,
    success_general,
    success_lambda0,
)

CLAIMS_PATH = REPO_ROOT / "claims.json"

# ANALYTIC golden values from the implemented formulas
#   overlap(d)  = (2 - d) / d
#   p_helstrom  = 1/2 * (1 + sqrt(1 - overlap^2))
#   p_simple    = 1 - overlap^2 / 2
GOLDEN = {
    4: {"overlap": -0.5, "simple": 0.875, "helstrom": 0.9330127018922193},
    16: {"overlap": -0.875, "simple": 0.6171875, "helstrom": 0.7420614591379635},
    64: {"overlap": -0.96875, "simple": 0.53076171875, "helstrom": 0.6240195927061527},
    256: {"overlap": -0.9921875, "simple": 0.507781982421875, "helstrom": 0.5623778102448098},
}

# Historical printed values retained for audit; never display without checking.
PUBLISHED_D256 = {
    "simple": 0.5078125,
    "helstrom": 0.562378286,
    "separable": 1.0,
}


@pytest.mark.parametrize("d", sorted(GOLDEN))
def test_overlap_golden(d: int) -> None:
    assert overlap(d) == pytest.approx(GOLDEN[d]["overlap"], abs=1e-12)


@pytest.mark.parametrize("d", sorted(GOLDEN))
def test_simple_success_golden(d: int) -> None:
    assert simple_success(d) == pytest.approx(GOLDEN[d]["simple"], abs=1e-12)


@pytest.mark.parametrize("d", sorted(GOLDEN))
def test_helstrom_ceiling_golden(d: int) -> None:
    assert helstrom_ceiling(d) == pytest.approx(GOLDEN[d]["helstrom"], abs=1e-12)


def test_golden_dimension_list_matches_fixtures() -> None:
    assert list(GOLDEN_DIMENSIONS) == [4, 16, 64, 256]


def test_separable_success_is_perfect() -> None:
    assert SEPARABLE_SUCCESS == 1.0


@pytest.mark.parametrize(
    "bad",
    [0, -2, -256, 3, 5, 6, 12, 100, 255, 1023, 2.5, "16", None],
)
def test_invalid_dimension_raises_value_error(bad: object) -> None:
    with pytest.raises(ValueError):
        overlap(bad)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        simple_success(bad)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        helstrom_ceiling(bad)  # type: ignore[arg-type]


@pytest.mark.parametrize("d", sorted(GOLDEN))
def test_value_ranges(d: int) -> None:
    ov = overlap(d)
    assert -1.0 <= ov <= 1.0
    assert 0.5 <= simple_success(d) <= 1.0
    assert simple_success(d) <= helstrom_ceiling(d) <= 1.0


def test_published_d256_helstrom_matches_formula_to_published_precision() -> None:
    """The spec prints the d=256 ceiling as ~0.562378286 (7+ digits)."""
    assert helstrom_ceiling(256) == pytest.approx(
        PUBLISHED_D256["helstrom"], abs=1e-6
    )


def test_published_d256_simple_figure_does_not_match_spec_formula() -> None:
    """The spec prints 0.5078125 for d=256; its own formula gives a different value.

    Recorded here as an explicit, visible discrepancy rather than silently
    choosing one number. The formula result is what the kernel returns; the
    printed figure is preserved verbatim in claims.json as
    `flagship_simple_maxent_d256_printed`.
    """
    formula_value = simple_success(256)
    printed_value = PUBLISHED_D256["simple"]
    assert formula_value == pytest.approx(0.507781982421875, abs=1e-12)
    assert printed_value == 0.5078125
    # NOT within the 1e-12 tolerance the plan Step 1 asks for.
    assert abs(formula_value - printed_value) > 1e-12


# ---------------------------------------------------------------- V oracle


def _operator(circuit):
    from qiskit.quantum_info import Operator

    return Operator(circuit).data


def _statevector(circuit) -> np.ndarray:
    from qiskit.quantum_info import Statevector

    return np.asarray(Statevector(circuit).data).reshape(-1)


def _fidelity(actual: np.ndarray, expected: np.ndarray) -> float:
    """State fidelity |<expected|actual>|^2; global-phase insensitive."""
    return float(np.abs(np.vdot(expected, actual)) ** 2)


def _basis(index: int, size: int) -> np.ndarray:
    vector = np.zeros(size, dtype=complex)
    vector[index] = 1.0
    return vector


@pytest.mark.parametrize("num_system_qubits", [2, 4])
def test_v_oracle_fixes_zero_state(num_system_qubits: int) -> None:
    """V|0...0> = +|0...0>."""
    state = _statevector(build_v_oracle(num_system_qubits, num_system_qubits))
    expected = _basis(0, 2**num_system_qubits)
    assert _fidelity(state, expected) == pytest.approx(1.0, abs=1e-12)


@pytest.mark.parametrize("num_system_qubits", [2, 4])
def test_v_oracle_negates_other_basis_states(num_system_qubits: int) -> None:
    """V|x> = -|x> for every x != 0...0 (compared via fidelity, not vectors)."""
    size = 2**num_system_qubits
    unitary = _operator(build_v_oracle(num_system_qubits, num_system_qubits))
    for index in range(1, size):
        prepared = _basis(index, size)
        result = unitary @ prepared
        assert _fidelity(result, prepared) == pytest.approx(1.0, abs=1e-12)
        # With the declared global phase applied the sign is exactly -1.
        assert result[index] == pytest.approx(-1.0, abs=1e-12)


@pytest.mark.parametrize("num_system_qubits", [1, 2, 3, 4, 5, 6, 7, 8])
def test_v_oracle_matches_definition_and_is_unitary(num_system_qubits: int) -> None:
    """d=256 (8 qubits) is one instance; no dimension is hard-coded."""
    size = 2**num_system_qubits
    unitary = _operator(build_v_oracle(num_system_qubits, num_system_qubits))
    assert np.abs(unitary - v_unitary_matrix(num_system_qubits)).max() < 1e-12
    assert np.abs(unitary.conj().T @ unitary - np.eye(size)).max() < 1e-12


def test_v_oracle_plus_to_minus_for_separable_probe() -> None:
    """V|+> = -|-> up to global phase on the two-basis-state probe."""
    num_system_qubits = 2
    size = 2**num_system_qubits
    plus = _basis(0, size) / np.sqrt(2) + _basis(size - 1, size) / np.sqrt(2)
    minus = _basis(0, size) / np.sqrt(2) - _basis(size - 1, size) / np.sqrt(2)

    result = _operator(build_v_oracle(num_system_qubits, num_system_qubits)) @ plus
    assert _fidelity(result, minus) == pytest.approx(1.0, abs=1e-12)


def test_v_oracle_pads_to_total_qubits_with_idle_zero() -> None:
    num_system_qubits, total_qubits = 4, 8
    circuit = build_v_oracle(num_system_qubits, total_qubits)
    assert circuit.num_qubits == total_qubits
    touched = {
        circuit.find_bit(qubit).index
        for instruction in circuit.data
        for qubit in instruction.qubits
    }
    assert touched == set(range(num_system_qubits))

    prepared = QuantumCircuit(total_qubits)
    prepared.h(0)
    state = _statevector(
        prepared.compose(build_v_oracle(num_system_qubits, total_qubits))
    )
    # Qiskit is little-endian: qubits n..total-1 are the higher-order bits, so
    # any amplitude with index >= 2**n would mean an idle qubit left |0>.
    assert np.allclose(state[2**num_system_qubits :], 0.0, atol=1e-12)


def test_v_oracle_rejects_bad_arguments() -> None:
    with pytest.raises(ValueError):
        build_v_oracle(8, 4)
    with pytest.raises(ValueError):
        build_v_oracle(0, 4)
    with pytest.raises(ValueError):
        build_v_oracle(2.0, 4)
    with pytest.raises(ValueError):
        build_v_oracle(-2, 4)


# -------------------------------------------------------------- claims.json

REQUIRED_CLAIM_FIELDS = ("id", "kind", "value", "source", "reproduced", "safe_for_demo")
VALID_KINDS = {"EMPIRICAL", "ANALYTIC", "THEORETICAL_CEILING"}


def _claims() -> dict:
    return json.loads(CLAIMS_PATH.read_text(encoding="utf-8"))


def test_claims_json_parses_and_has_claims() -> None:
    data = _claims()
    assert isinstance(data["claims"], list) and data["claims"]
    ids = [claim["id"] for claim in data["claims"]]
    assert len(ids) == len(set(ids))


def test_every_claim_declares_required_fields() -> None:
    for claim in _claims()["claims"]:
        missing = [field for field in REQUIRED_CLAIM_FIELDS if field not in claim]
        assert not missing, f"{claim.get('id')} missing {missing}"


def test_every_exposed_numeric_claim_declares_a_kind() -> None:
    for claim in _claims()["claims"]:
        assert claim["kind"] in VALID_KINDS, f"{claim['id']} has kind {claim['kind']}"
        assert isinstance(claim["value"], (int, float))
        assert isinstance(claim["source"], str) and claim["source"]
        assert isinstance(claim["reproduced"], bool)
        assert isinstance(claim["safe_for_demo"], bool)


def test_claims_json_frozen_d256_values() -> None:
    by_id = {claim["id"]: claim for claim in _claims()["claims"]}
    assert by_id["flagship_overlap_maxent_d256"]["value"] == -0.9921875
    assert by_id["flagship_separable_d256"]["value"] == 1.0
    assert by_id["flagship_helstrom_maxent_d256"]["kind"] == "THEORETICAL_CEILING"
    assert by_id["flagship_helstrom_maxent_d256"]["value"] == helstrom_ceiling(256)


def test_claims_json_golden_dimensions_are_present() -> None:
    claims = _claims()["claims"]
    covered = {
        (claim.get("dimension"), claim.get("formula", "").split("(")[0])
        for claim in claims
    }
    for dimension in GOLDEN_DIMENSIONS:
        assert any(item[0] == dimension for item in covered)


def test_claims_json_marks_historical_figure_unsafe_for_demo() -> None:
    by_id = {claim["id"]: claim for claim in _claims()["claims"]}
    printed = by_id["flagship_simple_maxent_d256_printed"]
    assert printed["reproduced"] is False
    assert printed["safe_for_demo"] is False


def _phrase_positions(text: str, phrase: str):
    start = 0
    while True:
        index = text.find(phrase, start)
        if index < 0:
            return
        yield index
        start = index + len(phrase)


def _negated(prefix: str) -> bool:
    """True when the phrase is inside an explicit negation such as 'no '/'not '."""
    return any(
        prefix.rstrip().endswith(word)
        for word in ("no", "not", "never", "neither", "nor")
    )


_FORBIDDEN_NOVELTY_PHRASES = (
    "we discovered",
    "we have discovered",
    "quantum advantage",
    "quantum computational advantage",
    "breakthrough",
    "first time",
    "new theorem",
)


def test_claims_json_avoids_novelty_claims() -> None:
    """No discovery-of-theorem or quantum-advantage language in exposed copy."""
    text = CLAIMS_PATH.read_text(encoding="utf-8").lower()
    for phrase in _FORBIDDEN_NOVELTY_PHRASES:
        # A negated mention ("no quantum advantage") is required framing, not a
        # claim; only unqualified affirmative uses are forbidden.
        for index in _phrase_positions(text, phrase):
            prefix = text[max(0, index - 12) : index]
            assert _negated(prefix), (
                f"claims.json contains unqualified forbidden phrase: {phrase!r} "
                f"(prefix {prefix!r})"
            )
    # The allowed, non-overclaiming framing must be present.
    assert "reproduces and operationalizes" in text


@pytest.mark.parametrize(
    "module", ["quantum/science.py", "quantum/oracles.py"], ids=str
)
def test_kernel_modules_avoid_novelty_language(module: str) -> None:
    """No discovery-of-theorem or quantum-advantage wording, comments included."""
    text = (REPO_ROOT / module).read_text(encoding="utf-8").lower()
    for phrase in _FORBIDDEN_NOVELTY_PHRASES:
        for index in _phrase_positions(text, phrase):
            prefix = text[max(0, index - 12) : index]
            assert _negated(prefix), f"{module} contains {phrase!r} (prefix {prefix!r})"


def test_claims_json_analytic_values_match_kernel() -> None:
    for claim in _claims()["claims"]:
        if not claim.get("safe_for_demo") or claim["kind"] == "EMPIRICAL":
            continue
        dimension = claim["dimension"]
        formula = claim["formula"]
        if formula.startswith("overlap(d)"):
            assert claim["value"] == pytest.approx(overlap(dimension), abs=1e-12)
        elif formula.startswith("p_simple(d)"):
            assert claim["value"] == pytest.approx(simple_success(dimension), abs=1e-12)


# ------------------------------------------------- generalized discrimination
#
# The flagship formulas above are the `I` vs `V` specialization of the general
# channel-discrimination mathematics. The functions under test here are
# PROVED AGAINST SIMULATION in this file: every expectation below is checked
# against an explicit Helstrom computation built from output density matrices
# with `numpy.linalg.eigvalsh`, which shares no code with the kernel.

GENERAL_DIMENSIONS = (4, 16, 64)


def _maxent_reduced_state(d: int) -> np.ndarray:
    """Reduced state of the max-entanglement probe: the maximally mixed state."""
    return np.eye(d, dtype=complex) / d


def _maxent_probe_vector(d: int) -> np.ndarray:
    """Explicit max-ent probe |Phi_d> on the reference x system registers."""
    vector = np.zeros(d * d, dtype=complex)
    for k in range(d):
        vector[k * d + k] = 1.0 / np.sqrt(d)
    return vector


def _v_matrix(d: int) -> np.ndarray:
    return v_unitary_matrix(d.bit_length() - 1)


def _diagonal_phase_unitary(d: int, theta: float) -> np.ndarray:
    """`diag(1, e^{i*theta}, ..., e^{i*(d-1)*theta})` -- a second unitary pair."""
    return np.diag(
        np.array([np.exp(1j * theta * k) for k in range(d)], dtype=complex)
    )


def _helstrom_from_output_states(u_matrix, v_matrix, probe) -> float:
    """Optimal success from EXPLICIT output density matrices.

    `P = 1/2 (1 + 1/2 ||rho_U - rho_V||_1)`, with the trace norm taken as the
    sum of the absolute eigenvalues of the Hermitian difference. This is the
    textbook Helstrom bound and never calls the kernel functions.
    """
    dim = u_matrix.shape[0]
    identity = np.eye(dim, dtype=complex)
    outputs = []
    for matrix in (u_matrix, v_matrix):
        vector = np.kron(identity, matrix) @ probe
        outputs.append(np.outer(vector, np.conj(vector)))
    difference = outputs[0] - outputs[1]
    eigenvalues = np.linalg.eigvalsh(difference)
    return 0.5 * (1.0 + 0.5 * float(np.abs(eigenvalues).sum()))


@pytest.mark.parametrize("d", GENERAL_DIMENSIONS)
def test_success_general_maxent_matches_helstrom_ceiling(d: int) -> None:
    """I vs V at max-entanglement: the general formula recovers the flagship."""
    rho_maxent = _maxent_reduced_state(d)
    assert success_general(rho_maxent, _v_matrix(d)) == pytest.approx(
        helstrom_ceiling(d), abs=1e-9
    )


@pytest.mark.parametrize("d", GENERAL_DIMENSIONS)
def test_success_general_maxent_matches_simulation(d: int) -> None:
    """The same value also comes out of explicit output-state Helstrom."""
    probe = _maxent_probe_vector(d)
    u_matrix, v_matrix = np.eye(d, dtype=complex), _v_matrix(d)
    simulated = _helstrom_from_output_states(u_matrix, v_matrix, probe)
    assert success_general(_maxent_reduced_state(d), u_matrix.conj().T @ v_matrix) == (
        pytest.approx(simulated, abs=1e-9)
    )
    assert simulated == pytest.approx(helstrom_ceiling(d), abs=1e-9)


@pytest.mark.parametrize("d", GENERAL_DIMENSIONS)
def test_success_lambda0_maxent_matches_helstrom_ceiling(d: int) -> None:
    """`lambda_0 = 1/d` (the max-ent smallest eigenvalue) reproduces the ceiling."""
    assert maxent_lambda0(d) == 1.0 / d
    assert success_lambda0(maxent_lambda0(d)) == pytest.approx(
        helstrom_ceiling(d), abs=1e-9
    )
    assert success_lambda0(maxent_lambda0(d)) == pytest.approx(
        success_general(_maxent_reduced_state(d), _v_matrix(d)), abs=1e-9
    )


def test_success_lambda0_and_overlap_agree_for_max_entanglement() -> None:
    """The `lambda_0` and `W` parametrizations coincide at `lambda_0 = 1/d`.

    `overlap(d) = (2 - d)/d = 2 * (1/d) - 1 = 2 * lambda_0 - 1`, so both
    closed forms evaluate the same `sqrt(1 - overlap^2)`.
    """
    for d in GENERAL_DIMENSIONS:
        assert maxent_lambda0(d) * 2.0 - 1.0 == pytest.approx(overlap(d), abs=1e-12)


@pytest.mark.parametrize("d", (2, 4, 8, 16, 64, 256))
def test_success_lambda0_half_is_exactly_one(d: int) -> None:
    """`success_lambda0(1/2)` is bit-exactly `1.0`, independent of dimension."""
    assert success_lambda0(0.5) == 1.0
    assert success_lambda0(1.0 / 2.0) == 1.0


@pytest.mark.parametrize("d", (2, 4, 8, 16, 64))
def test_success_lambda0_half_is_attained_by_a_diagonal_unitary_pair(d: int) -> None:
    """`lambda_0 = 1/2` is realized at each `d`, and simulation confirms `P = 1`.

    `U = I`, `V = diag(e^{i*2*pi*k/d})` gives `W` eigenvalues equal to the `d`
    roots of unity, whose sum is `0`. Then `Tr[rho_A W] = Tr[W]/d = 0`, i.e.
    `lambda_0 = (1 + 0)/2 = 1/2`, so the closed form must be `1` and the
    independently simulated Helstrom value must agree.
    """
    u_matrix = np.eye(d, dtype=complex)
    v_matrix = _diagonal_phase_unitary(d, 2.0 * np.pi / d)
    w_matrix = u_matrix.conj().T @ v_matrix
    assert abs(np.trace(w_matrix)) == pytest.approx(0.0, abs=1e-9)
    assert success_general(_maxent_reduced_state(d), w_matrix) == pytest.approx(
        success_lambda0(0.5), abs=1e-9
    )
    assert _helstrom_from_output_states(
        u_matrix, v_matrix, _maxent_probe_vector(d)
    ) == pytest.approx(1.0, abs=1e-9)


@pytest.mark.parametrize("theta", (0.35, 0.7, 1.1, 2.0, 2.9))
def test_success_general_second_unitary_pair_matches_simulation(theta: float) -> None:
    """A second unitary pair at d=4, checked against independent Helstrom."""
    d = 4
    u_matrix = np.eye(d, dtype=complex)
    v_matrix = _diagonal_phase_unitary(d, theta)
    w_matrix = u_matrix.conj().T @ v_matrix
    simulated = _helstrom_from_output_states(
        u_matrix, v_matrix, _maxent_probe_vector(d)
    )
    assert simulated < 1.0 - 1e-6, "this pair must be non-trivially imperfect"
    assert success_general(_maxent_reduced_state(d), w_matrix) == pytest.approx(
        simulated, abs=1e-9
    )


def test_separable_probe_reaches_unit_success_for_identity_v() -> None:
    """The two-basis-state separable probe makes `P = 1` for `I` vs `V`.

    `rho_A = |+><+|` has an overlap of exactly 0 with the hull: the hull of the
    eigenvalues of `V` is the segment from `-1` to `+1`, and `0` is a hull point
    (the midpoint of that segment), which is what the separable probe attains.
    """
    d = 4
    v_matrix = _v_matrix(d)
    plus = np.zeros(d, dtype=complex)
    plus[0] = plus[1] = 1.0 / np.sqrt(2.0)
    rho_separable = np.outer(plus, np.conj(plus))

    overlap_magnitude = abs(np.trace(rho_separable @ v_matrix))
    assert overlap_magnitude == pytest.approx(0.0, abs=1e-12)

    centroid, hull = centroid_and_hull(np.linalg.eigvals(v_matrix))
    # The hull midpoint of the eigenvalue segment is the attainable 0 overlap.
    assert abs((hull[0] + hull[1]) / 2.0) == pytest.approx(0.0, abs=1e-12)
    assert abs(centroid) == pytest.approx(abs(overlap(d)), abs=1e-12)

    assert success_general(rho_separable, v_matrix) == pytest.approx(1.0, abs=1e-12)
    # Independent simulation of the same product probe agrees.
    assert _helstrom_from_output_states(
        np.eye(d, dtype=complex), v_matrix, np.kron(plus, plus)
    ) == pytest.approx(1.0, abs=1e-9)


# ------------------------------------------------------------ centroid & hull


def test_scipy_availability_is_recorded() -> None:
    """Records whether `scipy.spatial.ConvexHull` is usable in this environment."""
    try:
        import scipy.spatial  # noqa: F401

        available = True
    except ImportError:  # pragma: no cover - environment dependent
        available = False
    assert SCIPY_AVAILABLE is available


@pytest.mark.parametrize("d", GENERAL_DIMENSIONS)
def test_centroid_of_identity_v_eigenvalues_predicts_max_ent_helstrom(d: int) -> None:
    """The exact relation implemented and proved numerically.

    For `I` vs `V`, `W = V` is Hermitian with eigenvalues `{+1, -1, ..., -1}`, so
    its centroid is `(1 - (d - 1)) / d = (2 - d) / d`, i.e. the centroid IS the
    flagship overlap (no extra factor of `d`):

        |centroid| = |overlap(d)|   and   P = 1/2 (1 + sqrt(1 - |centroid|^2))

    This is `success_general(I/d, W)` because `trace(I/d @ W) = trace(W)/d`, and
    the mean of the eigenvalues is `trace(W)/d`. No factor is inserted.
    """
    v_matrix = _v_matrix(d)
    centroid, hull = centroid_and_hull(np.linalg.eigvals(v_matrix))
    assert centroid == pytest.approx(complex(overlap(d)), abs=1e-12)
    assert abs(centroid) == pytest.approx(abs(overlap(d)), abs=1e-12)

    # Independent numerical confirmation of the identity above.
    predicted = 0.5 * (1.0 + np.sqrt(max(0.0, 1.0 - abs(centroid) ** 2)))
    assert float(predicted) == pytest.approx(helstrom_ceiling(d), abs=1e-9)
    assert float(predicted) == pytest.approx(
        success_general(_maxent_reduced_state(d), v_matrix), abs=1e-9
    )
    assert float(predicted) == pytest.approx(success_lambda0(maxent_lambda0(d)), abs=1e-9)

    # The hull of `{+1, -1 x (d-1)}` is the segment `[-1, +1]`.
    assert sorted(round(abs(z), 12) for z in hull) == [1.0, 1.0]


@pytest.mark.parametrize("theta", (0.35, 0.7, 1.1, 2.0))
def test_centroid_of_second_unitary_pair_matches_simulation(theta: float) -> None:
    """For a general unitary pair the centroid relation also holds numerically.

    For max entanglement `trace(I/d @ W) = trace(W)/d = mean(eigenvalues)`, so
    `success_general(I/d, W) = 1/2 (1 + sqrt(1 - |centroid|^2))` for any unitary
    pair whose `W = U^dag V` has unit-modulus eigenvalues. Verified here against
    the explicit Helstrom value rather than asserted from a formula.
    """
    d = 4
    u_matrix = np.eye(d, dtype=complex)
    v_matrix = _diagonal_phase_unitary(d, theta)
    w_matrix = u_matrix.conj().T @ v_matrix
    centroid, _hull = centroid_and_hull(np.linalg.eigvals(w_matrix))
    predicted = 0.5 * (1.0 + np.sqrt(max(0.0, 1.0 - abs(centroid) ** 2)))
    simulated = _helstrom_from_output_states(
        u_matrix, v_matrix, _maxent_probe_vector(d)
    )
    assert float(predicted) == pytest.approx(simulated, abs=1e-9)


def test_centroid_and_hull_vertices_are_in_angular_order() -> None:
    d = 4
    theta = 0.7
    centroid, hull = centroid_and_hull(
        np.linalg.eigvals(_diagonal_phase_unitary(d, theta))
    )
    assert len(hull) >= 3, "d distinct unit-circle points form a non-degenerate hull"
    angles = [float(np.angle(z)) % (2.0 * np.pi) for z in hull]
    assert angles == sorted(angles)
    for vertex in hull:
        assert abs(abs(vertex) - 1.0) == pytest.approx(0.0, abs=1e-12)
        # Every hull vertex is an eigenvalue of W.
        assert vertex in set(np.linalg.eigvals(_diagonal_phase_unitary(d, theta)))


def test_centroid_is_the_mean_of_the_eigenvalues() -> None:
    d = 8
    theta = 1.3
    eigenvalues = np.linalg.eigvals(_diagonal_phase_unitary(d, theta))
    centroid, _hull = centroid_and_hull(eigenvalues)
    assert centroid == pytest.approx(complex(np.mean(eigenvalues)), abs=1e-12)


def test_centroid_and_hull_handles_repeated_eigenvalues() -> None:
    """Degenerate hull (fewer than 3 distinct points) must not raise."""
    _centroid, hull = centroid_and_hull(np.linalg.eigvals(_v_matrix(4)))
    assert len(hull) == 2
    assert sorted(round(z.real, 12) for z in hull) == [-1.0, 1.0]


def test_centroid_and_hull_rejects_non_unit_modulus() -> None:
    with pytest.raises(ValueError):
        centroid_and_hull(np.array([1.0, 0.5 + 0.0j]))


def test_centroid_and_hull_rejects_empty_input() -> None:
    with pytest.raises(ValueError):
        centroid_and_hull(np.array([], dtype=complex))


# ------------------------------------------------------------- input guards


def test_success_general_rejects_bad_input() -> None:
    good = np.eye(2, dtype=complex)
    with pytest.raises(ValueError):  # non-square
        success_general(np.ones((2, 3), dtype=complex), good)
    with pytest.raises(ValueError):  # mismatched dimensions
        success_general(np.eye(3, dtype=complex), good)
    with pytest.raises(ValueError):  # trace != 1
        success_general(np.eye(2, dtype=complex) / 4.0, good)
    with pytest.raises(ValueError):  # not positive semidefinite
        not_psd = np.diag(np.array([2.0, -1.0])).astype(complex)
        success_general(not_psd, good)
    with pytest.raises(ValueError):  # not Hermitian
        not_hermitian = np.array([[0.5, 0.2j], [0.1j, 0.5]], dtype=complex)
        success_general(not_hermitian, good)
    with pytest.raises(ValueError):  # W not unitary
        success_general(np.eye(2, dtype=complex) / 2, np.eye(2, dtype=complex) * 2)


def test_success_general_accepts_valid_input_and_is_bounded() -> None:
    rng = np.random.default_rng(20260907)
    d = 4
    rho = np.eye(d, dtype=complex) / d
    matrix = rng.normal(size=(d, d)) + 1j * rng.normal(size=(d, d))
    q, r = np.linalg.qr(matrix)
    unitary = q * (np.diag(r) / np.abs(np.diag(r)))
    value = success_general(rho, unitary)
    assert 0.5 <= value <= 1.0


@pytest.mark.parametrize("bad", (-0.1, 1.1, 2.0, -1.0, float("nan")))
def test_success_lambda0_rejects_out_of_range(bad: float) -> None:
    with pytest.raises(ValueError):
        success_lambda0(bad)


def test_success_lambda0_endpoints_are_chance() -> None:
    assert success_lambda0(0.0) == 0.5
    assert success_lambda0(1.0) == 0.5


@pytest.mark.parametrize("d", (2, 4, 16, 64, 256))
def test_maxent_lambda0_is_one_over_d(d: int) -> None:
    assert maxent_lambda0(d) == 1.0 / d


def test_maxent_lambda0_rejects_invalid_dimension() -> None:
    with pytest.raises(ValueError):
        maxent_lambda0(3)
