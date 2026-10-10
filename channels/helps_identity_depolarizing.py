"""HELPS pair: identity I versus the qubit depolarizing channel.

For this pair the maximally entangled Helstrom optimum is higher than the
separable optimum, the opposite ordering to the flagship HURTS pair. The
numbers are derived from the trace norm of the two channel outputs. The
maximally-entangled 0.875 value is a theoretical ceiling here; this module does
not claim that the project implements the corresponding measurement strategy.

The optional qiskit-aer dependency is imported only when the local depolarizing
circuit is actually constructed. Metadata and analytic gallery rendering stay
usable in a Qollab runtime that provides Qiskit but not Aer.
"""

from __future__ import annotations

from typing import Dict, Tuple

import numpy as np
from qiskit import QuantumCircuit

from channels.api import ChannelPair, Strategy

__all__ = [
    "HELPS_DIMENSION",
    "HELPS_PAIR",
    "HELPS_SLUG",
    "HELPSIdentityDepolarizing",
    "depolarizing_lambda",
    "entangled_ceiling",
    "separable_value",
]

HELPS_SLUG = "helps-identity-depolarizing"
HELPS_DIMENSION = 2
_LAMBDA = 1.0


def depolarizing_lambda() -> float:
    """Depolarizing strength lambda used by channel B."""
    return _LAMBDA


def _helstrom_from(delta: np.ndarray) -> float:
    """Equal-prior Helstrom success probability from a state difference matrix."""
    trace_norm = float(np.abs(np.linalg.eigvalsh(delta)).sum())
    return 0.5 + 0.25 * trace_norm


def separable_value() -> float:
    """Helstrom success for the declared separable |0> probe."""
    lam = depolarizing_lambda()
    zero = np.array([1.0, 0.0])
    identity_output = np.outer(zero, zero)
    depolarized_output = lam * np.eye(2) / 2 + (1 - lam) * identity_output
    return _helstrom_from(identity_output - depolarized_output)


def entangled_ceiling() -> float:
    """Helstrom optimum for a Bell probe against full depolarization."""
    lam = depolarizing_lambda()
    bell = np.array([1.0, 0.0, 0.0, 1.0]) / np.sqrt(2.0)
    phi = np.outer(bell, bell.conj())
    identity_output = phi
    depolarized_output = lam * np.eye(4) / 4 + (1 - lam) * phi
    return _helstrom_from(identity_output - depolarized_output)


class HELPSIdentityDepolarizing(ChannelPair):
    """Identity versus a fully depolarizing single-qubit channel."""

    name = "Identity vs Depolarizing"
    slug = HELPS_SLUG
    citation = (
        "Standard quantum channel-discrimination bound: for identity versus a "
        "depolarizing channel the Bell probe has Helstrom optimum "
        "1/2 + 1/4 ||rho_I - rho_D||_1. The value is reproduced locally from "
        "the trace-norm derivation; the optimum measurement is not implemented "
        "as a live Qollab strategy here."
    )
    dimension = HELPS_DIMENSION

    def build_a(self, num_system_qubits: int, total_qubits: int) -> QuantumCircuit:
        """Channel A is the identity: a padded circuit with no gates."""
        _check_widths(num_system_qubits, total_qubits)
        return QuantumCircuit(total_qubits, name="I")

    def build_b(self, num_system_qubits: int, total_qubits: int) -> QuantumCircuit:
        """Build the optional local Aer depolarizing instruction."""
        _check_widths(num_system_qubits, total_qubits)
        if num_system_qubits != 1:
            raise ValueError(
                "the depolarizing channel is applied to a single system qubit"
            )
        from qiskit_aer.noise import depolarizing_error

        circuit = QuantumCircuit(total_qubits, name="depolarizing")
        circuit.append(depolarizing_error(depolarizing_lambda(), 1), [0])
        return circuit

    def strategies(self) -> Tuple[Strategy, ...]:
        bounds = self.analytic_bounds()
        return (
            Strategy(
                slug="helps-separable",
                label="SEPARABLE",
                probe_kind="SEPARABLE",
                bound_kind="ANALYTIC",
                analytic_value=bounds["separable"],
                claim_ids=("helps_depolarizing_separable_d2",),
            ),
            Strategy(
                slug="helps-max-entanglement",
                label="MAX ENTANGLEMENT OPTIMUM",
                probe_kind="MAX_ENTANGLEMENT",
                bound_kind="THEORETICAL_CEILING",
                analytic_value=bounds["helstrom_ceiling"],
                claim_ids=("helps_depolarizing_max_entangled_d2",),
            ),
        )

    def analytic_bounds(self) -> Dict[str, float]:
        """Trace-norm-derived values at the declared qubit dimension."""
        ceiling = entangled_ceiling()
        return {
            "separable": separable_value(),
            # Kept as a compatibility alias for earlier fixtures. It is not an
            # executable-strategy claim; strategies() labels it as a ceiling.
            "max_entanglement_simple": ceiling,
            "helstrom_ceiling": ceiling,
        }


def _check_widths(num_system_qubits: int, total_qubits: int) -> None:
    if total_qubits < num_system_qubits:
        raise ValueError(
            f"total_qubits ({total_qubits}) must cover the {num_system_qubits}-qubit "
            "system register"
        )


HELPS_PAIR = HELPSIdentityDepolarizing()
