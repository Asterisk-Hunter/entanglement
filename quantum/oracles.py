"""Unitary construction of the `V` channel for qubit registers.

`V = 2|0...0><0...0| - I` is Hermitian and unitary. On an `n`-qubit register
(`d = 2**n`) it is diagonal with `+1` on `|0...0>` and `-1` on every other
computational-basis state.

Construction, with no hard-coded dimension:

    W = 2|1...1><1...1| - I                 (diag(-1, ..., -1, +1))
    P = H(n-1) . MCX(n-1 controls) . H(n-1)  (multi-controlled Z, diag(1,...,1,-1))
    V = -X^n . P . X^n                       (bit-flip conjugation, then exp(i*pi))

`X^n` conjugation moves the single `+1` eigenvalue from `|1...1>` to
`|0...0>`, giving `-V`; the declared global phase `pi` supplies the remaining
minus sign so the circuit realises `V` exactly.

For `n == 1` the multi-controlled phase degenerates to a single `Z` and no
global phase is required.

Global phase: declared as `V_GLOBAL_PHASE`. Oracle tests compare physical state
equivalence / fidelity and never phase-strict vector equality.
"""

from __future__ import annotations

import math

from qiskit import QuantumCircuit
from qiskit.circuit.library import MCXGate

__all__ = [
    "V_GLOBAL_PHASE",
    "build_v_oracle",
    "v_unitary_matrix",
]

#: Declared global phase of the constructed oracle, `exp(i*pi) = -1`.
V_GLOBAL_PHASE: float = math.pi


def _require_positive_int(value: int, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{name} must be a positive integer, got {value!r}")
    return value


def build_v_oracle(num_system_qubits: int, total_qubits: int) -> QuantumCircuit:
    """Build the `V = 2|0...0><0...0| - I` oracle on a padded register.

    The oracle acts on qubits `0 .. num_system_qubits - 1`. The remaining
    `total_qubits - num_system_qubits` qubits receive no gates, so they stay in
    `|0>` and are expected to measure `0`.

    The dimension is never hard-coded: `d = 2 ** num_system_qubits`.
    """
    n = _require_positive_int(num_system_qubits, "num_system_qubits")
    total = _require_positive_int(total_qubits, "total_qubits")
    if total < n:
        raise ValueError(
            f"total_qubits ({total}) must be >= num_system_qubits ({n})"
        )

    circuit = QuantumCircuit(total, name=f"V_d{2**n}")

    if n == 1:
        circuit.z(0)
        return circuit

    target = n - 1
    controls = list(range(target))
    for qubit in range(n):
        circuit.x(qubit)
    circuit.h(target)
    circuit.append(MCXGate(target), controls + [target])
    circuit.h(target)
    for qubit in range(n):
        circuit.x(qubit)

    circuit.global_phase = V_GLOBAL_PHASE
    return circuit


def v_unitary_matrix(num_system_qubits: int):
    """Dense `2**n x 2**n` matrix of `V`, for analytic comparison in tests."""
    import numpy as np

    n = _require_positive_int(num_system_qubits, "num_system_qubits")
    size = 2**n
    matrix = -np.eye(size, dtype=complex)
    matrix[0, 0] = 1.0
    return matrix