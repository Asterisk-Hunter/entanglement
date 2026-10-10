"""Analytic kernel for the one-query channel-discrimination game.

The formulas here reproduce the verified values for the flagship channel pair
(identity `I` versus `V = 2|0...0><0...0| - I`) with a maximally entangled probe
of dimension `d`, as specified in the design spec. Every number returned by
this module is an ANALYTIC value; none of them is a measurement.

Formulas (design spec, "Human-verified science"):

    overlap(d)       = (2 - d) / d
    p_helstrom(d)    = 1/2 * (1 + sqrt(1 - overlap(d)^2))
    p_simple(d)      = 1 - overlap(d)^2 / 2

The separable strategy with the two basis states is perfect for this pair, so
its success probability is the constant `SEPARABLE_SUCCESS`.
"""

from __future__ import annotations

import math
from typing import Sequence, Tuple

__all__ = [
    "GOLDEN_DIMENSIONS",
    "SCIPY_AVAILABLE",
    "SEPARABLE_SUCCESS",
    "centroid_and_hull",
    "helstrom_ceiling",
    "is_valid_dimension",
    "maxent_lambda0",
    "overlap",
    "simple_success",
    "success_general",
    "success_lambda0",
]

#: Dimensions used for golden regression fixtures across the product.
GOLDEN_DIMENSIONS: tuple[int, ...] = (4, 16, 64, 256)

#: The separable two-basis-state probe wins every round for this channel pair.
SEPARABLE_SUCCESS: float = 1.0

#: Absolute tolerance for the density-matrix validation in `success_general`.
TOLERANCE: float = 1e-9

try:  # pragma: no cover - presence depends on the environment
    from scipy.spatial import ConvexHull as _ConvexHull

    #: `True` when `scipy.spatial.ConvexHull` is importable here.
    SCIPY_AVAILABLE: bool = True
except ImportError:  # pragma: no cover - documented fallback, see below
    _ConvexHull = None
    SCIPY_AVAILABLE = False


def is_valid_dimension(d: int) -> bool:
    """Return True when `d` is a positive power of two.

    Only powers of two are supported because the flagship circuits are built
    from qubit registers.
    """
    return isinstance(d, int) and not isinstance(d, bool) and d >= 1 and (d & (d - 1)) == 0


def _require_dimension(d: int) -> int:
    if not is_valid_dimension(d):
        raise ValueError(
            f"dimension must be a positive power of two, got {d!r}"
        )
    return d


def overlap(d: int) -> float:
    """Overlap of the two channel outputs for a maximal-entanglement probe."""
    d = _require_dimension(d)
    return (2 - d) / d


def helstrom_ceiling(d: int) -> float:
    """THEORETICAL_CEILING success probability for the probe at dimension `d`."""
    value = overlap(d)
    return 0.5 * (1.0 + math.sqrt(1.0 - value * value))


def simple_success(d: int) -> float:
    """ANALYTIC success probability of the executable simple strategy."""
    value = overlap(d)
    return 1.0 - (value * value) / 2.0


# --------------------------------------------------------- general channel case
#
# The flagship formulas above are the `I` vs `V` specialization of the general
# two-channel discrimination mathematics. For a pair of channels with the
# equal prior 1/2, let `W = U^dag V` be the unitary relating the two channels
# and let `rho_A` be the reduced state of the probe on the reference system. The
# Helstrom bound over states with reduced state `rho_A` is
#
#     P(rho_A, W) = 1/2 (1 + sqrt(1 - |Tr[rho_A W]|^2))
#
# and the bound over *all* reduced states is obtained by maximizing
# `|Tr[rho_A W]|`, which equals the largest eigenvalue of `W` in modulus. Writing
# `lambda_0` for that extremal value and using
# `max_{rho_A} |Tr[rho_A W]| = sqrt(1 - 4*lambda_0*(1 - lambda_0))` gives the
# equivalent eigenvalue-parametrized form
#
#     P(lambda_0) = 1/2 (1 + 2*sqrt(lambda_0*(1 - lambda_0)))
#
# These are UPPER BOUNDS for the given `rho_A` / `lambda_0`; the attained value
# depends on whether the extremizing reduced state is realizable. For the
# maximally entangled probe `rho_A = I/d` the bound is attained, and
# `lambda_0 = 1/d` for a unitary `W` whose eigenvalues all have modulus one.
#
# Every function below is verified against an explicit Helstrom computation in
# `tests/test_science.py`; none of them touches the flagships above.


def _as_square_matrix(value, name: str):
    """Return `value` as a square complex ndarray or raise ValueError."""
    import numpy as np

    try:
        matrix = np.asarray(value, dtype=complex)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be a numeric matrix: {error}") from error
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError(f"{name} must be a square 2-D matrix, got shape {matrix.shape}")
    return matrix


def _require_density_matrix(rho: "object", name: str) -> None:
    """Reject anything that is not a trace-one positive semidefinite state."""
    import numpy as np

    matrix = _as_square_matrix(rho, name)
    if matrix.shape[0] == 0:
        raise ValueError(f"{name} must have positive dimension")
    if np.max(np.abs(matrix - matrix.conj().T)) > TOLERANCE:
        raise ValueError(f"{name} must be Hermitian")
    if abs(np.trace(matrix) - 1.0) > TOLERANCE:
        raise ValueError(f"{name} must have trace one, got {np.trace(matrix)!r}")
    if float(np.min(np.linalg.eigvalsh(matrix))) < -TOLERANCE:
        raise ValueError(f"{name} must be positive semidefinite")


def success_general(rho_A, W) -> float:
    """HELSTROM bound for probe reduced state `rho_A` and channel pair `W`.

        P = 1/2 * (1 + sqrt(max(0, 1 - |Tr[rho_A W]|^2)))

    `W = U^dag V`. `rho_A` must be a Hermitian, trace-one, positive semidefinite
    matrix and `W` must be a square unitary of the same dimension; anything
    else raises ValueError.
    """
    import numpy as np

    rho = _as_square_matrix(rho_A, "rho_A")
    unitary = _as_square_matrix(W, "W")
    _require_density_matrix(rho, "rho_A")
    if rho.shape != unitary.shape:
        raise ValueError(
            f"rho_A and W must share a dimension, got {rho.shape} and {unitary.shape}"
        )
    identity = np.eye(unitary.shape[0], dtype=complex)
    if np.max(np.abs(unitary.conj().T @ unitary - identity)) > TOLERANCE:
        raise ValueError("W must be unitary")

    overlap_magnitude = abs(complex(np.trace(rho @ unitary)))
    inside = max(0.0, 1.0 - overlap_magnitude**2)
    return 0.5 * (1.0 + math.sqrt(inside))


def success_lambda0(lambda_0: float) -> float:
    """Eigenvalue-parametrized HELSTROM bound.

        P = 1/2 * (1 + 2*sqrt(lambda_0*(1 - lambda_0)))

    `lambda_0` is the extremal `|Tr[rho_A W]|` eigenvalue in `[0, 1]`. This
    parametrization reproduces `helstrom_ceiling(d)` at `lambda_0 = 1/d`,
    i.e. at `lambda_0 = maxent_lambda0(d)`, and is exactly `1.0` at
    `lambda_0 = 1/2`.
    """
    if isinstance(lambda_0, bool) or not isinstance(lambda_0, (int, float)):
        raise ValueError(f"lambda_0 must be a real number in [0, 1], got {lambda_0!r}")
    value = float(lambda_0)
    if not math.isfinite(value) or value < 0.0 or value > 1.0:
        raise ValueError(f"lambda_0 must lie in [0, 1], got {lambda_0!r}")
    return 0.5 * (1.0 + 2.0 * math.sqrt(value * (1.0 - value)))


def maxent_lambda0(d: int) -> float:
    """`lambda_0` for the maximally entangled probe, `1/d`."""
    return 1.0 / _require_dimension(d)


def centroid_and_hull(eigenvalues: Sequence[complex]) -> Tuple[complex, Tuple[complex, ...]]:
    """Centroid and convex-hull vertices of the eigenvalues of a unitary `W`.

    `eigenvalues` must be a non-empty sequence of unit-modulus complex numbers.
    Returns `(centroid, hull_vertices)` where the centroid is the arithmetic
    mean and the vertices are the convex-hull vertices in increasing angular
    order.

    `scipy.spatial.ConvexHull` is used when importable. When it is absent, or
    when the point set is degenerate (fewer than three distinct points, as for
    the flagship `V` whose spectrum is `{+1, -1, ..., -1}`), the fallback is the
    set of distinct points itself, which is the convex hull in every such case.
    """
    import numpy as np

    try:
        values = np.asarray(list(eigenvalues), dtype=complex)
    except (TypeError, ValueError) as error:
        raise ValueError(f"eigenvalues must be numeric: {error}") from error
    if values.ndim != 1 or values.size == 0:
        raise ValueError(
            f"eigenvalues must be a non-empty 1-D sequence, got shape {values.shape}"
        )
    if np.max(np.abs(np.abs(values) - 1.0)) > 1e-9:
        raise ValueError("eigenvalues must all have modulus one")

    centroid = complex(np.mean(values))
    points = np.unique(np.column_stack((values.real, values.imag)), axis=0)
    if SCIPY_AVAILABLE and points.shape[0] >= 3:
        try:
            vertices = points[_ConvexHull(points).vertices]
        except Exception:  # pragma: no cover - qhull degeneracy fallback
            vertices = points
    else:
        vertices = points
    ordered = sorted(
        (complex(point[0], point[1]) for point in vertices),
        key=lambda z: math.atan2(z.imag, z.real) % (2.0 * math.pi),
    )
    return centroid, tuple(ordered)