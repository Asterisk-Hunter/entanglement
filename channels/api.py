"""Extensible quantum channel-pair API.

Every experiment in the laboratory is a :class:`ChannelPair`: two channels A
and B that a player must distinguish with a single query. Engine and UI code
consume the common payload schema; a shipped pair is made discoverable by one
explicit registry entry here.

The registry is intentionally lazy. Qollab guarantees Qiskit but does not load
optional packages merely because another experiment might need them. Loading or
listing the flagship HURTS pair therefore must not import the HELPS
implementation (or any optional development dependency it may use for local
circuit construction).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from importlib import import_module
from typing import Dict, Tuple

from qiskit import QuantumCircuit

__all__ = [
    "BOUND_KINDS",
    "PROBE_KINDS",
    "ChannelPair",
    "Strategy",
    "available_pairs",
    "load_pair",
    "pair_payload",
    "registered_pair_payloads",
]

PROBE_KINDS: Tuple[str, ...] = ("SEPARABLE", "MAX_ENTANGLEMENT")
BOUND_KINDS: Tuple[str, ...] = ("ANALYTIC", "THEORETICAL_CEILING")


@dataclass(frozen=True)
class Strategy:
    """One probe strategy plus the theory number the UI may show for it."""

    slug: str
    label: str
    probe_kind: str
    bound_kind: str
    analytic_value: float
    claim_ids: Tuple[str, ...] = ()

    def to_payload(self) -> dict:
        data = asdict(self)
        data["claim_ids"] = list(self.claim_ids)
        return data


class ChannelPair(ABC):
    """Common experiment interface."""

    name: str
    slug: str
    citation: str
    dimension: int

    @abstractmethod
    def build_a(self, num_system_qubits: int, total_qubits: int) -> QuantumCircuit:
        """Circuit applying channel A to the system register."""

    @abstractmethod
    def build_b(self, num_system_qubits: int, total_qubits: int) -> QuantumCircuit:
        """Circuit applying channel B to the system register."""

    @abstractmethod
    def strategies(self) -> Tuple[Strategy, ...]:
        """Probe strategies with their analytic values and claim ids."""

    @abstractmethod
    def analytic_bounds(self) -> Dict[str, float]:
        """Analytic bounds at the pair's declared reference dimension."""

    def analytic_bounds_for(self, dimension: int) -> Dict[str, float]:
        """Analytic bounds at ``dimension`` when the pair supports it.

        Fixed-dimension pairs inherit this conservative default. Parametric
        pairs override it explicitly, which prevents the engine from silently
        reusing d=256 theory for a d=64 runtime batch.
        """
        if dimension != self.dimension:
            raise ValueError(
                f"{self.slug} defines analytic bounds only at d={self.dimension}, "
                f"got d={dimension}"
            )
        return self.analytic_bounds()


# slug -> (module, exported singleton, gallery role). Keeping this metadata
# dependency-free means discovery itself never imports qiskit_aer.
_PAIR_REGISTRY: Dict[str, Tuple[str, str, str]] = {
    "hurts-identity-v": ("channels.hurts_identity_v", "HURTS_PAIR", "FLAGSHIP"),
    "helps-identity-depolarizing": (
        "channels.helps_identity_depolarizing",
        "HELPS_PAIR",
        "COMPARATOR",
    ),
    "comparator-four-pauli": ("channels.four_pauli", "FOUR_PAULI_PAIR", "COMPARATOR"),
}


def load_pair(slug: str) -> ChannelPair:
    """Return the pair registered under ``slug``, importing only that pair."""
    try:
        module_name, export_name, _role = _PAIR_REGISTRY[slug]
    except KeyError:
        raise KeyError(slug) from None
    module = import_module(module_name)
    pair = getattr(module, export_name)
    if not isinstance(pair, ChannelPair):
        raise TypeError(f"registered pair {slug!r} is not a ChannelPair")
    return pair


def available_pairs() -> Tuple[str, ...]:
    """Sorted slugs without importing any pair implementation."""
    return tuple(sorted(_PAIR_REGISTRY))


def pair_payload(pair: ChannelPair) -> dict:
    """JSON-serializable science snapshot with no per-pair branching."""
    return {
        "name": pair.name,
        "slug": pair.slug,
        "citation": pair.citation,
        "dimension": pair.dimension,
        "strategies": [strategy.to_payload() for strategy in pair.strategies()],
        "bounds": dict(pair.analytic_bounds()),
    }


def _serialize_circuit(circuit: QuantumCircuit) -> dict:
    instructions = []
    for instruction in circuit.data:
        operation = instruction.operation
        qubits = [circuit.find_bit(qubit).index for qubit in instruction.qubits]
        suffix = " " + ",".join(str(index) for index in qubits) if qubits else ""
        instructions.append(f"{operation.name.upper()}{suffix}")
    return {
        "status": "AVAILABLE",
        "name": circuit.name,
        "global_phase": str(circuit.global_phase),
        "instructions": instructions,
    }


def _circuit_payload(pair: ChannelPair, total_qubits: int = 16) -> dict:
    """Best-effort expert circuit disclosure without making gallery discovery fail.

    Optional local-only dependencies may be absent in Qollab. In that case the
    science metadata still renders and the circuit disclosure states the
    limitation instead of inventing an executable path.
    """
    num_system_qubits = pair.dimension.bit_length() - 1
    channels = []
    for channel, builder in (("A", pair.build_a), ("B", pair.build_b)):
        try:
            circuit = builder(num_system_qubits, total_qubits)
            snapshot = _serialize_circuit(circuit)
        except (ImportError, ModuleNotFoundError) as exc:
            snapshot = {
                "status": "OPTIONAL DEPENDENCY UNAVAILABLE",
                "name": channel,
                "global_phase": "NOT REPORTED",
                "instructions": [],
                "limitation": f"{type(exc).__name__}: optional local circuit dependency unavailable",
            }
        snapshot["channel"] = channel
        channels.append(snapshot)
    return {
        "total_qubits": total_qubits,
        "system_qubits": num_system_qubits,
        "channels": channels,
    }


def registered_pair_payloads() -> list[dict]:
    """Return the generic resource-lab payload for every registered pair."""
    entries = []
    for slug in available_pairs():
        _module, _export, role = _PAIR_REGISTRY[slug]
        pair = load_pair(slug)
        payload = pair_payload(pair)
        payload["role"] = role
        payload["circuit"] = _circuit_payload(pair)
        entries.append(payload)
    return entries
