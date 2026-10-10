"""HURTS flagship pair: identity I versus V = 2|0...0><0...0| - I.

At the flagship dimension the maximally entangled probe performs worse than the
separable probe. Every analytic number here is read from the verified science
kernel so the pair cannot drift from the frozen formulas.
"""

from __future__ import annotations

from typing import Dict, Tuple

from qiskit import QuantumCircuit

from channels.api import ChannelPair, Strategy
from quantum import science
from quantum.oracles import build_v_oracle

__all__ = ["HURTS_DIMENSION", "HURTS_PAIR", "HURTS_SLUG", "HURTSIdentityV"]

HURTS_SLUG = "hurts-identity-v"
HURTS_DIMENSION = 256


class HURTSIdentityV(ChannelPair):
    """Identity versus the V channel on a padded register."""

    name = "Identity vs V"
    slug = HURTS_SLUG
    citation = (
        "Reproduces and operationalizes the channel-discrimination result of "
        "Lien & Quintino (2026); maximal entanglement can reduce discrimination "
        "success for this channel pair."
    )
    dimension = HURTS_DIMENSION

    def build_a(self, num_system_qubits: int, total_qubits: int) -> QuantumCircuit:
        """Channel A is the identity: a padded circuit with no gates."""
        _check_widths(num_system_qubits, total_qubits)
        return QuantumCircuit(total_qubits, name="I")

    def build_b(self, num_system_qubits: int, total_qubits: int) -> QuantumCircuit:
        """Channel B is V, built by the shared oracle builder."""
        _check_widths(num_system_qubits, total_qubits)
        return build_v_oracle(num_system_qubits, total_qubits)

    def strategies(self) -> Tuple[Strategy, ...]:
        bounds = self.analytic_bounds()
        return (
            Strategy(
                slug="hurts-separable",
                label="SEPARABLE",
                probe_kind="SEPARABLE",
                bound_kind="ANALYTIC",
                analytic_value=bounds["separable"],
                claim_ids=("flagship_separable_d256",),
            ),
            Strategy(
                slug="hurts-max-entanglement",
                label="MAX ENTANGLEMENT",
                probe_kind="MAX_ENTANGLEMENT",
                bound_kind="ANALYTIC",
                analytic_value=bounds["max_entanglement_simple"],
                claim_ids=("flagship_simple_maxent_d256_formula",),
            ),
        )

    def analytic_bounds(self) -> Dict[str, float]:
        """Bounds at the declared d=256 flagship dimension."""
        return self.analytic_bounds_for(self.dimension)

    def analytic_bounds_for(self, dimension: int) -> Dict[str, float]:
        """Bounds at any supported power-of-two runtime dimension."""
        if not science.is_valid_dimension(dimension) or dimension < 2:
            raise ValueError(
                f"dimension must be a power of two >= 2, got {dimension!r}"
            )
        return {
            "separable": science.SEPARABLE_SUCCESS,
            "overlap": science.overlap(dimension),
            "max_entanglement_simple": science.simple_success(dimension),
            "helstrom_ceiling": science.helstrom_ceiling(dimension),
        }


def _check_widths(num_system_qubits: int, total_qubits: int) -> None:
    if total_qubits < num_system_qubits:
        raise ValueError(
            f"total_qubits ({total_qubits}) must cover the {num_system_qubits}-qubit "
            "system register"
        )


HURTS_PAIR = HURTSIdentityV()
