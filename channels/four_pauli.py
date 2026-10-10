"""FOUR-PAULI pair: a unitary comparator with an attaining Bell readout.

Setting
-------
Two players share the maximally entangled pair :math:`|\\Phi^+\\rangle`. Channel A
applies :math:`R_P(2\\theta)` and channel B applies :math:`R_P(-2\\theta)` to the
system half, where

    R_P(phi) = exp(-i phi P / 2),   P in {X, Y, Z}

and :math:`W = A^\\dagger B = R_P(-4\\theta)`. The two channel outputs overlap by
:math:`\\cos(2\\theta)`, so the equal-prior Helstrom optimum is

    p_star(theta) = 1/2 * (1 + sin(2 theta))

Executable discriminator
------------------------
:func:`bell_discriminator_circuit` is the superdense-coding readout: prepare
``|Phi+>``, apply the channel to the system qubit, apply the Pauli-frame
correction :data:`DECODERS` to the reference qubit, then Bell-measure and answer
"A" exactly when the ``|Phi+>`` outcome appears. That two-outcome measurement is
the positive-eigenvalue projector of :math:`\\rho_A - \\rho_B`, so the circuit
attains ``p_star`` exactly (statevector exactness, asserted in
``tests/test_four_pauli.py``).

Because the measurement that attains the optimum is implemented and tested, the
max-entanglement strategy is published as ``ANALYTIC``, not
``THEORETICAL_CEILING``. A separable ``|+>`` probe with a Y-basis measurement
attains the same optimum. The Bell readout alone scores only 1/2 with a product
probe, which is a restriction of that measurement and does not establish a
resource advantage.

Nothing here is measured on hardware and nothing is sampled; every number is a
closed-form or exact-statevector value.
"""

from __future__ import annotations

import math
from typing import Dict, Tuple

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import UnitaryGate
from qiskit.quantum_info import Statevector

from channels.api import ChannelPair, Strategy
from quantum import science

__all__ = [
    "DECODERS",
    "FOUR_PAULI_DIMENSION",
    "FOUR_PAULI_PAIR",
    "FOUR_PAULI_SLUG",
    "FOUR_PAULI_THETA",
    "PAULI_GENERATORS",
    "FourPauliPair",
    "bell_discriminator_circuit",
    "bell_discriminator_probabilities",
    "bell_discriminator_success",
    "channel_matrix",
    "four_pauli_star",
    "pauli_matrix",
    "separable_star",
]

FOUR_PAULI_SLUG = "comparator-four-pauli"

#: The pair acts on a single system qubit; the reference qubit carries the probe.
FOUR_PAULI_DIMENSION = 2

#: Published reference angle: 2 * theta = pi/4, so p_star = (1 + 1/sqrt2)/2.
FOUR_PAULI_THETA = math.pi / 8

#: The four single-qubit Pauli generators. The discriminating pair uses the three
#: non-identity ones; the identity generator is the degenerate member listed so
#: the alphabet is complete (see `pauli_matrix`).
PAULI_GENERATORS: Tuple[str, ...] = ("I", "X", "Y", "Z")

#: Generators that define a non-degenerate pair.
_ACTIVE_GENERATORS: Tuple[str, ...] = ("X", "Y", "Z")

#: Pauli-frame correction applied to the REFERENCE qubit before the Bell
#: measurement, keyed by generator. Each entry is (gate, angle) where angle is
#: None for the parameterless S-dagger gate.
DECODERS: Dict[str, Tuple[str, float | None]] = {
    "X": ("rx", -math.pi / 2.0),
    "Y": ("ry", math.pi / 2.0),
    "Z": ("sdg", None),
}

_PAULI_MATRICES: Dict[str, np.ndarray] = {
    "X": np.array([[0, 1], [1, 0]], dtype=complex),
    "Y": np.array([[0, -1j], [1j, 0]], dtype=complex),
    "Z": np.array([[1, 0], [0, -1]], dtype=complex),
    "I": np.eye(2, dtype=complex),
}


def pauli_matrix(name: str) -> np.ndarray:
    """Return the single-qubit Pauli matrix `name` as a 2x2 complex array."""
    try:
        return _PAULI_MATRICES[name].copy()
    except KeyError:
        raise ValueError(
            f"generator must be one of {PAULI_GENERATORS}, got {name!r}"
        ) from None


def _require_generator(generator: str) -> str:
    if generator not in _ACTIVE_GENERATORS:
        raise ValueError(
            "generator must be one of " + ", ".join(_ACTIVE_GENERATORS)
            + f", got {generator!r}"
        )
    return generator


def _require_theta(theta: float) -> float:
    if isinstance(theta, bool) or not isinstance(theta, (int, float)):
        raise ValueError(f"theta must be a real number, got {theta!r}")
    value = float(theta)
    if not math.isfinite(value):
        raise ValueError(f"theta must be finite, got {theta!r}")
    if value < 0.0 or value > math.pi / 4.0:
        raise ValueError(
            f"theta must lie in [0, pi/4] so that sin(2 theta) is non-negative, got {theta!r}"
        )
    return value


def channel_matrix(generator: str, theta: float, sign: int) -> np.ndarray:
    """Return the channel unitary ``R_P(2 * sign * theta)``.

    ``sign`` is ``+1`` for channel A and ``-1`` for channel B, so the two
    channels are conjugates about the identity and ``W = A^dag B = R_P(-4 theta)``.
    """
    _require_generator(generator)
    value = _require_theta(theta)
    if sign not in (1, -1):
        raise ValueError(f"sign must be +1 or -1, got {sign!r}")
    matrix = pauli_matrix(generator)
    return math.cos(sign * value) * np.eye(2, dtype=complex) - 1j * math.sin(
        sign * value
    ) * matrix


def four_pauli_star(theta: float = FOUR_PAULI_THETA) -> float:
    """Closed-form Helstrom optimum ``1/2 * (1 + sin(2 theta))``.

    Read from the verified kernel rather than restated: with the maximally
    entangled probe the extremal reduced-state overlap is ``|Tr(I/d W)| =
    cos(theta)``, and :func:`quantum.science.success_lambda0` evaluates the
    eigenvalue-parametrized bound at ``lambda_0 = cos(theta)**2``.
    """
    value = _require_theta(theta)
    return science.success_lambda0(math.cos(value) ** 2)


def separable_star(theta: float = FOUR_PAULI_THETA) -> float:
    """Optimal product-probe success, equal to the max-entangled optimum."""
    _require_theta(theta)
    return four_pauli_star(theta)


def bell_discriminator_circuit(
    theta: float,
    sign: int,
    generator: str,
    total_qubits: int = 16,
) -> QuantumCircuit:
    """The executable superdense-coding discriminator, padded to `total_qubits`.

    Qubit 0 is the system register (the channel acts here); qubit 1 is the
    reference qubit held by the other player. Padding qubits are left idle.
    """
    _require_generator(generator)
    value = _require_theta(theta)
    if total_qubits < 2:
        raise ValueError(
            f"total_qubits must be at least 2 for the Bell readout, got {total_qubits!r}"
        )
    if sign not in (1, -1):
        raise ValueError(f"sign must be +1 or -1, got {sign!r}")

    circuit = QuantumCircuit(total_qubits, 2, name=f"four_pauli_{generator}_{sign:+d}")
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.append(
        UnitaryGate(channel_matrix(generator, value, sign), label="channel"),
        [0],
    )
    gate, angle = DECODERS[generator]
    if gate == "rx":
        circuit.rx(float(angle), 1)
    elif gate == "ry":
        circuit.ry(float(angle), 1)
    else:
        circuit.sdg(1)
    circuit.cx(1, 0)
    circuit.h(1)
    circuit.measure(0, 0)
    circuit.measure(1, 1)
    return circuit


def bell_discriminator_probabilities(
    theta: float,
    generator: str,
) -> Dict[int, Dict[str, float]]:
    """Exact measurement distribution of the discriminator under each channel.

    Keys are ``{"A": ..., "B": ...}`` for the hidden channel; inner keys are
    ``"phi_plus"`` and ``"other"``. Values are exact statevector probabilities,
    not samples.
    """
    _require_generator(generator)
    result: Dict[int, Dict[str, float]] = {}
    for sign, name in ((1, "A"), (-1, "B")):
        circuit = bell_discriminator_circuit(theta, sign, generator, total_qubits=2)
        bare = circuit.remove_final_measurements(inplace=False)
        distribution = Statevector.from_instruction(bare).probabilities_dict()
        phi_plus = 0.0
        other = 0.0
        for bits, probability in distribution.items():
            # Qiskit prints the bitstring most-significant qubit first, so the
            # last character is qubit 0 and the first is qubit 1. The Phi+
            # outcome is "qubit 0 reads 0 and qubit 1 reads 0".
            text = "".join(str(bits).split())
            if text[-1] == "0" and text[-2] == "0":
                phi_plus += float(probability)
            else:
                other += float(probability)
        result[name] = {"phi_plus": phi_plus, "other": other}
    return result


def bell_discriminator_success(
    theta: float,
    generator: str,
) -> float:
    """Win probability the executable discriminator attains, exactly.

    Answers "A" when the Bell measurement returns ``|Phi+>``; that two-outcome
    measurement is the positive-eigenvalue projector of ``rho_A - rho_B``, which
    is the Helstrom measurement for this pair.
    """
    probabilities = bell_discriminator_probabilities(theta, generator)
    return 0.5 * (
        probabilities["A"]["phi_plus"] + probabilities["B"]["other"]
    )


class FourPauliPair(ChannelPair):
    """Pauli-rotation pair whose optimal product and Bell probes tie."""

    name = "Four-Pauli Rotation Pair"
    slug = FOUR_PAULI_SLUG
    citation = (
        "Unitary channel comparator. With a shared maximally entangled pair and "
        "the two channels R_P(+2 theta) and R_P(-2 theta) applied to one half, the "
        "equal-prior Helstrom optimum is 1/2 (1 + sin 2 theta). The value is read "
        "from quantum.science and the optimum is attained here by an executable "
        "Bell-measurement discriminator (a Pauli-frame correction followed by a Bell "
        "readout), verified by exact statevector simulation. A separable |+> probe "
        "with a Y-basis readout attains the same value, so this pair is neutral "
        "under an optimal comparison of probe resources."
    )
    dimension = FOUR_PAULI_DIMENSION

    #: The published reference generator. All three agree numerically.
    generator = "Z"

    def build_a(self, num_system_qubits: int, total_qubits: int) -> QuantumCircuit:
        """Build channel A's positive Pauli rotation on a padded register."""
        _check_widths(num_system_qubits, total_qubits)
        circuit = QuantumCircuit(total_qubits, name="R_P_plus")
        circuit.append(
            UnitaryGate(channel_matrix(self.generator, FOUR_PAULI_THETA, 1), label="R_P_plus"),
            [0],
        )
        return circuit

    def build_b(self, num_system_qubits: int, total_qubits: int) -> QuantumCircuit:
        """Build channel B's negative Pauli rotation on a padded register."""
        _check_widths(num_system_qubits, total_qubits)
        circuit = QuantumCircuit(total_qubits, name="R_P_minus")
        circuit.append(
            UnitaryGate(channel_matrix(self.generator, FOUR_PAULI_THETA, -1), label="R_P_minus"),
            [0],
        )
        return circuit

    def strategies(self) -> Tuple[Strategy, ...]:
        bounds = self.analytic_bounds()
        return (
            Strategy(
                slug="four-pauli-separable",
                label="SEPARABLE OPTIMAL Y READOUT",
                probe_kind="SEPARABLE",
                bound_kind="ANALYTIC",
                analytic_value=bounds["separable"],
                claim_ids=("four_pauli_separable_optimum_theta_pi_8",),
            ),
            Strategy(
                slug="four-pauli-max-entanglement",
                label="MAX ENTANGLEMENT, BELL READOUT",
                probe_kind="MAX_ENTANGLEMENT",
                bound_kind="ANALYTIC",
                analytic_value=bounds["max_entanglement_simple"],
                claim_ids=("four_pauli_star_theta_pi_8",),
            ),
        )

    def analytic_bounds(self) -> Dict[str, float]:
        """Bounds at the published reference angle."""
        return self.analytic_bounds_for(self.dimension)

    def analytic_bounds_for(self, dimension: int) -> Dict[str, float]:
        """Bounds at the declared qubit dimension."""
        if not science.is_valid_dimension(dimension) or dimension != FOUR_PAULI_DIMENSION:
            raise ValueError(
                "the four-Pauli pair is defined only at "
                f"d={FOUR_PAULI_DIMENSION}, got d={dimension!r}"
            )
        return {
            "theta": float(FOUR_PAULI_THETA),
            "separable": separable_star(FOUR_PAULI_THETA),
            "max_entanglement_simple": four_pauli_star(FOUR_PAULI_THETA),
            "helstrom_ceiling": four_pauli_star(FOUR_PAULI_THETA),
        }


def _check_widths(num_system_qubits: int, total_qubits: int) -> None:
    if total_qubits < num_system_qubits:
        raise ValueError(
            f"total_qubits ({total_qubits}) must cover the {num_system_qubits}-qubit "
            "system register"
        )


FOUR_PAULI_PAIR = FourPauliPair()
