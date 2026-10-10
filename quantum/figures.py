"""Kernel data for the hull, heatmap, and dimension-sweep figures.

The three figures are rendered by ui/hull.js, ui/heatmap.js, and ui/sweep.js
from pinned fixtures. Every fixture here is derived from the verified
:mod:`quantum.science` kernel so the browser never computes physics.

Vocabulary
----------
* ``lambda_0`` is the extremal overlap ``|Tr[rho_A W]|`` used by
  :func:`quantum.science.success_general`.
* ``entropy`` is the von Neumann entropy of the probe's reduced state, i.e. the
  entanglement entropy of the pure joint probe.
* Fixed-basis curves keep the Schmidt basis pinned to the eigenbasis of ``V``.
* Best-aligned curves optimise the local basis by grid search over single-qubit
  rotations plus a refinement pass.

Honesty rules encoded here
--------------------------
* The separable hull-nearest point is attained by the flagship product-probe
  strategy. It is labelled ``ANALYTIC`` and carries ``attained_by_circuit: True``.
* The max-entanglement reachable point is the centroid of the spectrum.
* Dimensions above the live execution cap are flagged ``PRECOMPUTED``: their
  numbers are theory only and no circuit of that size is ever executed.
"""

from __future__ import annotations

import math
from typing import Dict, List, Sequence, Tuple

import numpy as np

from quantum import science
from quantum.engine import MAX_LIVE_DIMENSION

__all__ = [
    "FLAGSHIP_SPECTRUM",
    "HULL_DIMENSION",
    "LIVE_DIMENSIONS",
    "SWEEP_DIMENSIONS",
    "best_aligned_curve",
    "dimension_sweep",
    "eigenvalue_circle",
    "fixed_basis_curve",
    "heat_entropy",
    "heat_lambda_grid",
    "heat_success",
    "hull_centroid_and_vertices",
    "hull_point",
    "separable_hull_nearest",
    "unverified_heatmap_present",
]

#: The hull figure works at the default interactive dimension.
HULL_DIMENSION = 16

#: Dimensions the sweep draws. The last is above the live cap on purpose.
SWEEP_DIMENSIONS: Tuple[int, ...] = (2, 4, 16, 64, 256, 1024)

#: Dimensions a live one-backend-job run may actually execute.
LIVE_DIMENSIONS: Tuple[int, ...] = tuple(
    d for d in SWEEP_DIMENSIONS if d <= MAX_LIVE_DIMENSION
)

#: The flagship W = V has spectrum {+1, -1, -1, ...}: one +1 and d-1 minus ones.
FLAGSHIP_SPECTRUM: Tuple[complex, ...] = (1.0, -1.0)


def eigenvalue_circle(dimension: int) -> Dict[str, object]:
    """Unit-circle description of the flagship spectrum at `dimension`.

    ``points`` carries one entry per eigenvalue with its angle in radians and a
    multiplicity, so the renderer never has to guess how many eigenvalues sit at
    the same place. ``distinct`` is the deduplicated set the hull is built from.
    """
    if not science.is_valid_dimension(dimension) or dimension < 2:
        raise ValueError(f"dimension must be a power of two >= 2, got {dimension!r}")
    spectrum = [complex(1.0, 0.0)] + [complex(-1.0, 0.0)] * (dimension - 1)
    angles = [0.0] + [math.pi] * (dimension - 1)
    multiplicity: Dict[float, int] = {}
    for angle in angles:
        multiplicity[angle] = multiplicity.get(angle, 0) + 1
    points = [
        {
            "re": math.cos(angle),
            "im": math.sin(angle),
            "angle": angle,
            "multiplicity": count,
        }
        for angle, count in sorted(multiplicity.items())
    ]
    return {
        "dimension": dimension,
        "points": points,
        "distinct": [(1.0, 0.0), (-1.0, 0.0)],
        "radius": 1.0,
    }


def hull_centroid_and_vertices(dimension: int) -> Tuple[Dict[str, float], List[Dict[str, float]]]:
    """Centroid and angular-ordered hull vertices, read from the kernel."""
    spectrum = [complex(1.0, 0.0)] + [complex(-1.0, 0.0)] * (dimension - 1)
    centroid, vertices = science.centroid_and_hull(spectrum)
    return (
        {"re": centroid.real, "im": centroid.imag},
        [{"re": vertex.real, "im": vertex.imag} for vertex in vertices],
    )


def hull_point(centroid: Dict[str, float], vertices: Sequence[Dict[str, float]]):
    """Max-entanglement reachable point: the centroid of the spectrum.

    The maximally entangled probe has reduced state ``I/d``, so
    ``Tr[rho_A W]`` is exactly the mean of the eigenvalues. It is reachable, not
    a bound, so it is labelled ANALYTIC.
    """
    centroid_value = complex(centroid["re"], centroid["im"])
    return {
        "re": centroid_value.real,
        "im": centroid_value.imag,
        "modulus": abs(centroid_value),
        "kind": "ANALYTIC",
        "token": "ANALYTIC",
        "label": "MAX-ENT PROBE REACHABLE POINT",
        "attained_by_circuit": True,
        "vertices": len(vertices),
    }


def separable_hull_nearest(dimension: int) -> Dict[str, object]:
    """Point of the hull nearest the origin: the separable reachable set.

    The separable reachable set of ``Tr[rho_A W]`` is the convex hull of the
    spectrum, so the nearest hull point to the origin is the smallest overlap a
    separable probe can reach. For the flagship spectrum that hull contains the
    origin, so the smallest reachable overlap is exactly zero.

    The flagship product-probe discriminator attains this point: its two-basis
    readout distinguishes the channels perfectly. The overlap is therefore an
    ANALYTIC value with ``attained_by_circuit: True``.
    """
    centroid, vertices = hull_centroid_and_vertices(dimension)
    if len(vertices) < 2:
        raise ValueError("the flagship hull must have at least two vertices")
    del centroid
    # The nearest point of the hull is not always a vertex: for the flagship the
    # hull is the whole diameter, so the origin lies on an edge. Search the
    # vertices and every edge's interior, and take the closest point found.
    best = min(vertices, key=lambda v: math.hypot(v["re"], v["im"]))
    best_distance = math.hypot(best["re"], best["im"])
    count = len(vertices)
    for index in range(count):
        start = vertices[index]
        end = vertices[(index + 1) % count]
        point = _closest_point_on_segment(start, end)
        distance = math.hypot(point.real, point.imag)
        if distance < best_distance:
            best_distance = distance
            best = {"re": point.real, "im": point.imag}
    value = complex(best["re"], best["im"])
    modulus = abs(value)
    return {
        "re": value.real,
        "im": value.imag,
        "modulus": modulus,
        "kind": "ANALYTIC",
        "token": "ANALYTIC",
        "label": "SEPARABLE HULL-NEAREST POINT, EXECUTABLE",
        "attained_by_circuit": True,
        "success": science.SEPARABLE_SUCCESS,
        "dimension": dimension,
    }


# ----------------------------------------------------------------- heat map


def heat_entropy(spectrum: Sequence[float]) -> float:
    """Von Neumann entropy in bits of the given probability vector."""
    total = 0.0
    for probability in spectrum:
        if probability > 0.0:
            total -= probability * math.log2(probability)
    return total


def heat_lambda_grid() -> Tuple[float, ...]:
    """Overlap axis for the heat map, from 0 to 1 in 21 steps."""
    return tuple(round(index / 20.0, 4) for index in range(21))


def heat_success(lambda_0: float) -> float:
    """Helstrom bound at overlap ``lambda_0``, read from the kernel."""
    return science.success_lambda0(lambda_0)


def _spectrum_from_entropy(entropy: float, levels: int) -> Tuple[float, ...]:
    """Probability vector with `entropy` bits of entropy over `levels` levels.

    Uses a one-parameter geometric family, which spans the full entropy range
    from 0 (a single level holds everything) to ``log2(levels)`` (uniform). For a
    requested entropy that the family cannot reach at these levels, the closest
    attainable value is returned; callers compare against the actual value.
    """
    if levels < 2:
        raise ValueError("levels must be at least 2")
    maximum = math.log2(levels)
    entropy = min(max(entropy, 0.0), maximum)
    if entropy <= 0.0:
        return (1.0,) + (0.0,) * (levels - 1)
    if entropy >= maximum - 1e-12:
        return (1.0 / levels,) * levels
    low, high = 0.0, 1.0
    best = (1.0 / levels,) * levels
    for _ in range(200):
        ratio = (low + high) / 2.0
        weights = [ratio**index for index in range(levels)]
        total = sum(weights)
        probabilities = tuple(weight / total for weight in weights)
        value = heat_entropy(probabilities)
        if value < entropy:
            low = ratio
        else:
            high = ratio
        best = probabilities
    return best


def fixed_basis_curve(entropy: float, levels: int = 2) -> Dict[str, object]:
    """Overlap and bound at `entropy` with the Schmidt basis pinned.

    ``lambda_0`` is the overlap of the fixed-basis probe. Nothing is optimised
    here, so this curve is a plain reference line.
    """
    probabilities = _spectrum_from_entropy(entropy, levels)
    lambda_0 = _fixed_basis_overlap(probabilities, levels)
    return {
        "entropy": entropy,
        "lambda_0": lambda_0,
        "success": heat_success(lambda_0),
        "kind": "THEORETICAL_CEILING",
        "token": "THEORETICAL_CEILING",
    }


def _fixed_basis_overlap(probabilities: Sequence[float], levels: int) -> float:
    """Overlap for the pinned-basis probe at `levels`.

    ``V`` is ``diag(1, -1, ..., -1)`` so ``Tr[rho V] = 2 rho_00 - 1``. The
    pinned Schmidt basis puts the largest coefficient on the level ``V``
    eigenstates as ``+1``; the remainder sits on the ``-1`` levels.
    """
    return abs(2.0 * probabilities[0] - 1.0)


def _optimised_overlap(probabilities: Sequence[float], levels: int) -> float:
    """Overlap that maximises the bound after rotating the Schmidt basis.

    Explicit optimisation, not an assumption: for every pair of levels the search
    sweeps the angle of the single-qubit rotation that mixes them over a coarse
    grid, then refines around the best coarse sample by bisection.

    ``V`` singles out only the level-0 direction: ``Tr[rho V] = 2 rho_00 - 1``.
    Mixing levels ``0`` and ``k`` by an angle ``theta`` moves the population on
    the ``V`` ``+1`` eigenspace to

        p0' = p0 cos^2 + pk sin^2 + 2 sqrt(p0 pk) sin cos

    and the overlap becomes ``lambda_0 = |2 p0' - 1|``. The bound
    ``1/2 (1 + 2 sqrt(lambda_0 (1 - lambda_0)))`` peaks at ``lambda_0 = 1/2``, so
    the search minimises ``|lambda_0 - 1/2|``. The untouched basis is always a
    candidate, so the result can never score below the pinned basis.
    """
    best = _fixed_basis_overlap(probabilities, levels)
    if levels < 2:
        return best
    p0 = probabilities[0]
    coarse_step = math.pi / 36.0
    for other in range(1, levels):
        pk = probabilities[other]
        # Coarse pass: bracket the best coarse sample of |lambda_0 - 1/2|. The
        # bracket is chosen independently of the incumbent so a rotation is
        # always explored, even when the pinned basis is already near 1/2.
        coarse_distance = _alignment_distance(_mix_overlap(p0, pk, 0.0))
        coarse_angle = 0.0
        for index in range(1, 37):
            angle = index * coarse_step
            distance = _alignment_distance(_mix_overlap(p0, pk, angle))
            if distance < coarse_distance:
                coarse_distance = distance
                coarse_angle = angle
        # Refinement pass: bisect the bracket until the angle is resolved.
        best_angle = coarse_angle
        span = coarse_step
        for _ in range(40):
            left = best_angle - span
            right = best_angle + span
            if _alignment_distance(_mix_overlap(p0, pk, left)) < _alignment_distance(
                _mix_overlap(p0, pk, right)
            ):
                best_angle = left
            else:
                best_angle = right
            span /= 2.0
        for angle in (best_angle - span, best_angle, best_angle + span):
            candidate = _mix_overlap(p0, pk, angle)
            if _alignment_distance(candidate) < _alignment_distance(best):
                best = candidate
    return best


def _closest_point_on_segment(
    start: Dict[str, float], end: Dict[str, float]
) -> complex:
    """Point of the segment ``start``-``end`` nearest the origin."""
    a = complex(start["re"], start["im"])
    b = complex(end["re"], end["im"])
    direction = b - a
    denominator = direction.real**2 + direction.imag**2
    if denominator == 0.0:
        return a
    t = -(a.real * direction.real + a.imag * direction.imag) / denominator
    t = min(1.0, max(0.0, t))
    return a + t * direction


def _alignment_distance(lambda_0: float) -> float:
    """Distance from the overlap that maximises the Helstrom bound."""
    return abs(lambda_0 - 0.5)


def _mix_overlap(p0: float, pk: float, angle: float) -> float:
    """``|2 p0' - 1|`` after mixing levels 0 and k by `angle`."""
    cos = math.cos(angle)
    sin = math.sin(angle)
    coherence = 2.0 * math.sqrt(max(0.0, p0 * pk))
    population = p0 * cos * cos + pk * sin * sin + coherence * sin * cos
    return abs(2.0 * population - 1.0)


def best_aligned_curve(entropy: float, levels: int = 2) -> Dict[str, object]:
    """Overlap and bound at `entropy` after the explicit basis optimisation.

    This is a Helstrom bound for a rotated basis, not a measured value, so it is
    labelled THEORETICAL_CEILING like every other quantity in this module.
    """
    probabilities = _spectrum_from_entropy(entropy, levels)
    fixed = _fixed_basis_overlap(probabilities, levels)
    optimised = _optimised_overlap(probabilities, levels)
    if science.success_lambda0(optimised) < science.success_lambda0(fixed) - 1e-12:
        raise AssertionError(
            "best-aligned must never score below fixed-basis: "
            f"lambda_0 {optimised} vs {fixed} at entropy {entropy}"
        )
    return {
        "entropy": entropy,
        "lambda_0": optimised,
        "success": heat_success(optimised),
        "kind": "THEORETICAL_CEILING",
        "token": "THEORETICAL_CEILING",
        "fixed_lambda_0": fixed,
    }


def unverified_heatmap_present() -> bool:
    """Always ``False``.

    Both heat-map curves are Helstrom bounds over rotated bases. No circuit
    implements either, so neither is ever labelled executable.
    """
    return False


# ---------------------------------------------------------------- dimension sweep


def dimension_sweep() -> List[Dict[str, object]]:
    """One row per dimension in :data:`SWEEP_DIMENSIONS`, read from the kernel."""
    rows: List[Dict[str, object]] = []
    for dimension in SWEEP_DIMENSIONS:
        executable = science.simple_success(dimension)
        ceiling = science.helstrom_ceiling(dimension)
        rows.append(
            {
                "d": dimension,
                "separable": science.SEPARABLE_SUCCESS,
                "simple": executable,
                "ceiling": ceiling,
                "executable_kind": "ANALYTIC",
                "ceiling_kind": "THEORETICAL_CEILING",
                "live": dimension <= MAX_LIVE_DIMENSION,
                "source": "LIVE_KERNEL" if dimension <= MAX_LIVE_DIMENSION else "PRECOMPUTED",
                "trials": 4000,
                "standard_error": _standard_error(executable),
                "resolvable_from_chance": _resolvable(executable),
            }
        )
    return rows


def _standard_error(probability: float) -> float:
    """Standard error of a binomial estimate at 4000 trials."""
    trials = 4000
    return math.sqrt(max(0.0, probability * (1.0 - probability)) / trials)


def _resolvable(probability: float) -> bool:
    """True when the gap to chance clears two standard errors at 4000 trials."""
    return (probability - 0.5) > 2.0 * _standard_error(probability)
