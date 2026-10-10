"""Kernel tests for the hull, heat-map, and dimension-sweep figure data.

These pin every number the browser will draw against the verified
:mod:`quantum.science` kernel, and they enforce the honesty rules that the
renderers depend on:

* the separable hull-nearest point is attained by the flagship strategy;
* the max-entanglement reachable point is the centroid and is attainable;
* the best-aligned optimiser never loses to the fixed basis, and agrees with an
  independent brute-force search at a spot-checked point;
* the d=1024 sweep row is flagged precomputed, and d=256 is flagged as not
  resolvable from chance at 4000 trials.
"""

from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from quantum import figures, science  # noqa: E402
from quantum.engine import MAX_LIVE_DIMENSION  # noqa: E402

ENTROPY_POINTS = (0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0)
LEVELS = (2, 4, 8)
SWEEP_JS = REPO_ROOT / "ui" / "sweep.js"


# ------------------------------------------------------------------- spectrum


def test_flagship_spectrum_is_one_plus_and_many_minus() -> None:
    assert figures.FLAGSHIP_SPECTRUM == (1.0, -1.0)


@pytest.mark.parametrize("dimension", (2, 4, 16, 64))
def test_eigenvalue_circle_lists_the_unit_modulus_spectrum(dimension: int) -> None:
    circle = figures.eigenvalue_circle(dimension)
    assert circle["dimension"] == dimension
    assert circle["radius"] == 1.0
    points = circle["points"]
    assert len(points) == 2, "the flagship spectrum has two distinct points"
    total = sum(point["multiplicity"] for point in points)
    assert total == dimension
    for point in points:
        assert math.hypot(point["re"], point["im"]) == pytest.approx(1.0, abs=1e-12)
    assert points[0]["angle"] == pytest.approx(0.0, abs=1e-12)
    assert points[1]["angle"] == pytest.approx(math.pi, abs=1e-12)
    assert points[0]["multiplicity"] == 1
    assert points[1]["multiplicity"] == dimension - 1


def test_eigenvalue_circle_rejects_bad_dimensions() -> None:
    for bad in (0, 3, -4, True):
        with pytest.raises(ValueError):
            figures.eigenvalue_circle(bad)


# ------------------------------------------------------------------------ hull


@pytest.mark.parametrize("dimension", (2, 4, 16, 64, 256))
def test_hull_centroid_matches_the_kernel(dimension: int) -> None:
    centroid, _vertices = figures.hull_centroid_and_vertices(dimension)
    spectrum = [complex(1.0, 0.0)] + [complex(-1.0, 0.0)] * (dimension - 1)
    expected, _ = science.centroid_and_hull(spectrum)
    assert complex(centroid["re"], centroid["im"]) == pytest.approx(expected, abs=1e-12)
    # The centroid is the maximally entangled probe's overlap.
    assert centroid["re"] == pytest.approx(science.overlap(dimension), abs=1e-12)
    assert centroid["im"] == pytest.approx(0.0, abs=1e-12)


@pytest.mark.parametrize("dimension", (2, 4, 16, 64))
def test_hull_vertices_are_in_angular_order(dimension: int) -> None:
    _centroid, vertices = figures.hull_centroid_and_vertices(dimension)
    assert len(vertices) == 2
    for vertex in vertices:
        assert math.hypot(vertex["re"], vertex["im"]) == pytest.approx(1.0, abs=1e-12)
    angles = [math.atan2(v["im"], v["re"]) % (2.0 * math.pi) for v in vertices]
    assert angles == sorted(angles)


def test_max_ent_point_is_the_centroid_and_is_attainable() -> None:
    centroid, vertices = figures.hull_centroid_and_vertices(figures.HULL_DIMENSION)
    point = figures.hull_point(centroid, vertices)
    assert point["re"] == pytest.approx(centroid["re"], abs=1e-12)
    assert point["im"] == pytest.approx(centroid["im"], abs=1e-12)
    assert point["kind"] == "ANALYTIC"
    assert point["token"] == "ANALYTIC"
    assert point["attained_by_circuit"] is True
    assert point["modulus"] == pytest.approx(abs(centroid["re"]), abs=1e-12)


def test_separable_hull_nearest_is_labelled_as_an_attained_analytic_value() -> None:
    point = figures.separable_hull_nearest(figures.HULL_DIMENSION)
    assert point["kind"] == "ANALYTIC"
    assert point["token"] == "ANALYTIC"
    assert point["attained_by_circuit"] is True
    assert "EXECUTABLE" in point["label"]
    # The flagship hull is the whole diameter, so the nearest point is the origin.
    assert point["modulus"] == pytest.approx(0.0, abs=1e-12)
    assert point["success"] == pytest.approx(1.0)


def test_separable_hull_nearest_is_always_called_executable() -> None:
    """Every supported flagship dimension has the same attaining strategy."""
    for dimension in (2, 4, 16, 64):
        point = figures.separable_hull_nearest(dimension)
        assert point["kind"] == "ANALYTIC"
        assert point["token"] == "ANALYTIC"
        assert point["attained_by_circuit"] is True
        assert point["success"] == pytest.approx(1.0)


def test_hull_points_lie_on_or_inside_the_unit_circle() -> None:
    centroid, vertices = figures.hull_centroid_and_vertices(figures.HULL_DIMENSION)
    max_ent = figures.hull_point(centroid, vertices)
    separable = figures.separable_hull_nearest(figures.HULL_DIMENSION)
    for point in (max_ent, separable):
        assert math.hypot(point["re"], point["im"]) <= 1.0 + 1e-12


# ------------------------------------------------------------------ entropy


@pytest.mark.parametrize("levels", LEVELS)
def test_entropy_of_a_uniform_spectrum_is_log2_levels(levels: int) -> None:
    uniform = (1.0 / levels,) * levels
    assert figures.heat_entropy(uniform) == pytest.approx(math.log2(levels), abs=1e-12)


def test_entropy_of_a_pure_spectrum_is_zero() -> None:
    assert figures.heat_entropy((1.0, 0.0)) == pytest.approx(0.0, abs=1e-12)
    assert figures.heat_entropy((0.0, 1.0, 0.0)) == pytest.approx(0.0, abs=1e-12)


def test_entropy_ignores_zero_probabilities() -> None:
    assert figures.heat_entropy((0.5, 0.5, 0.0, 0.0)) == pytest.approx(1.0, abs=1e-12)


@pytest.mark.parametrize("levels", LEVELS)
@pytest.mark.parametrize("entropy", ENTROPY_POINTS)
def test_spectrum_family_hits_the_requested_entropy(levels: int, entropy: float) -> None:
    spectrum = figures._spectrum_from_entropy(entropy, levels)
    assert len(spectrum) == levels
    assert sum(spectrum) == pytest.approx(1.0, abs=1e-12)
    assert all(value >= -1e-15 for value in spectrum)
    target = min(entropy, math.log2(levels))
    assert figures.heat_entropy(spectrum) == pytest.approx(target, abs=1e-9)


@pytest.mark.parametrize("entropy", ENTROPY_POINTS)
def test_success_reads_the_kernel(entropy: float) -> None:
    for lambda_0 in figures.heat_lambda_grid():
        assert figures.heat_success(lambda_0) == pytest.approx(
            science.success_lambda0(lambda_0), abs=0.0
        )


def test_lambda_grid_runs_zero_to_one() -> None:
    grid = figures.heat_lambda_grid()
    assert grid[0] == 0.0
    assert grid[-1] == 1.0
    assert grid == tuple(sorted(grid))
    assert len(grid) == 21


def test_success_is_maximal_at_the_half_overlap() -> None:
    assert figures.heat_success(0.5) == pytest.approx(1.0, abs=1e-12)
    assert figures.heat_success(0.0) == pytest.approx(0.5, abs=1e-12)
    assert figures.heat_success(1.0) == pytest.approx(0.5, abs=1e-12)


# ----------------------------------------------------------- the two curves


@pytest.mark.parametrize("levels", LEVELS)
@pytest.mark.parametrize("entropy", ENTROPY_POINTS)
def test_fixed_basis_curve_is_a_bound_and_matches_the_kernel(
    levels: int, entropy: float
) -> None:
    row = figures.fixed_basis_curve(entropy, levels)
    assert row["kind"] == "THEORETICAL_CEILING"
    assert row["token"] == "THEORETICAL_CEILING"
    assert 0.0 <= row["lambda_0"] <= 1.0
    assert row["success"] == pytest.approx(
        science.success_lambda0(row["lambda_0"]), abs=1e-12
    )


@pytest.mark.parametrize("levels", LEVELS)
@pytest.mark.parametrize("entropy", ENTROPY_POINTS)
def test_best_aligned_never_loses_to_fixed_basis(levels: int, entropy: float) -> None:
    """The grid requirement, enforced for every grid point."""
    fixed = figures.fixed_basis_curve(entropy, levels)
    aligned = figures.best_aligned_curve(entropy, levels)
    # The comparison is on the bound, not on lambda_0: the bound peaks at
    # lambda_0 = 1/2, so a rotation can raise lambda_0 and still win.
    assert aligned["success"] >= fixed["success"] - 1e-12
    assert aligned["fixed_lambda_0"] == pytest.approx(fixed["lambda_0"], abs=1e-15)
    assert aligned["success"] == pytest.approx(
        science.success_lambda0(aligned["lambda_0"]), abs=1e-12
    )


def test_best_aligned_is_itself_labelled_a_bound() -> None:
    row = figures.best_aligned_curve(0.5, 2)
    assert row["kind"] == "THEORETICAL_CEILING"
    assert row["token"] == "THEORETICAL_CEILING"


def _brute_force_bound(spectrum, levels: int) -> float:
    """Independent brute force for the best bound over the mixing family.

    Deliberately a different search: an exhaustive angle sweep with no
    refinement, scoring the bound itself. Agreement with the shipped grid-plus-
    refinement optimiser is therefore evidence rather than a tautology.
    """
    best = 0.0
    p0 = spectrum[0]
    for other in range(1, levels):
        pk = spectrum[other]
        for index in range(20001):
            angle = index * math.pi / 20000.0
            cos = math.cos(angle)
            sin = math.sin(angle)
            coherence = 2.0 * math.sqrt(max(0.0, p0 * pk))
            population = p0 * cos * cos + pk * sin * sin + coherence * sin * cos
            bound = science.success_lambda0(abs(2.0 * population - 1.0))
            if bound > best:
                best = bound
    return best


@pytest.mark.parametrize(
    "entropy,levels", [(0.3, 2), (0.5, 4), (0.7, 8), (0.9, 4), (0.25, 2)]
)
def test_best_aligned_matches_brute_force_at_spot_checked_points(
    entropy: float, levels: int
) -> None:
    spectrum = figures._spectrum_from_entropy(entropy, levels)
    aligned = figures.best_aligned_curve(entropy, levels)
    reference = _brute_force_bound(spectrum, levels)
    assert aligned["success"] == pytest.approx(reference, abs=1e-6)


def test_best_aligned_reaches_the_ideal_bound() -> None:
    """A rotation can always place the overlap at the bound's optimum, 1/2."""
    for entropy in (0.0, 0.3, 0.5, 0.9, 1.0):
        row = figures.best_aligned_curve(entropy, 2)
        assert row["lambda_0"] == pytest.approx(0.5, abs=1e-6)
        assert row["success"] == pytest.approx(1.0, abs=1e-6)


def test_unverified_heatmap_present_is_always_false() -> None:
    assert figures.unverified_heatmap_present() is False


# -------------------------------------------------------------------- sweep


def test_sweep_covers_exactly_the_requested_dimensions() -> None:
    rows = figures.dimension_sweep()
    assert [row["d"] for row in rows] == [2, 4, 16, 64, 256, 1024]
    assert figures.SWEEP_DIMENSIONS == (2, 4, 16, 64, 256, 1024)


@pytest.mark.parametrize("d", figures.SWEEP_DIMENSIONS)
def test_sweep_rows_come_from_the_kernel(d: int) -> None:
    row = next(item for item in figures.dimension_sweep() if item["d"] == d)
    assert row["separable"] == science.SEPARABLE_SUCCESS
    assert row["simple"] == pytest.approx(science.simple_success(d), abs=0.0)
    assert row["ceiling"] == pytest.approx(science.helstrom_ceiling(d), abs=0.0)
    assert row["executable_kind"] == "ANALYTIC"
    assert row["ceiling_kind"] == "THEORETICAL_CEILING"


def test_sweep_ceiling_is_never_below_the_executable_value() -> None:
    for row in figures.dimension_sweep():
        assert row["ceiling"] >= row["simple"]
        if row["d"] > 2:
            assert row["ceiling"] > row["simple"], "the gap opens past d=2"


def test_separable_curve_is_flat_and_never_below_the_executable_curve() -> None:
    rows = figures.dimension_sweep()
    assert {row["separable"] for row in rows} == {1.0}
    for row in rows:
        assert row["separable"] >= row["simple"]
        if row["d"] > 2:
            assert row["separable"] > row["simple"], "entanglement starts to hurt past d=2"


def test_executable_curve_falls_toward_chance_with_dimension() -> None:
    values = [row["simple"] for row in figures.dimension_sweep()]
    assert values == sorted(values, reverse=True)
    assert values[-1] > 0.5


def test_d1024_is_precomputed_and_never_live() -> None:
    row = next(item for item in figures.dimension_sweep() if item["d"] == 1024)
    assert row["live"] is False
    assert row["source"] == "PRECOMPUTED"
    assert 1024 > MAX_LIVE_DIMENSION


def test_every_sweep_dimension_at_or_below_the_cap_is_live() -> None:
    for row in figures.dimension_sweep():
        if row["d"] <= MAX_LIVE_DIMENSION:
            assert row["live"] is True
            assert row["source"] == "LIVE_KERNEL"
    assert figures.LIVE_DIMENSIONS == (2, 4, 16, 64, 256)


def test_standard_error_matches_the_binomial_formula() -> None:
    for row in figures.dimension_sweep():
        probability = row["simple"]
        expected = math.sqrt(probability * (1.0 - probability) / 4000.0)
        assert row["standard_error"] == pytest.approx(expected, abs=1e-15)
        assert row["trials"] == 4000


def test_d256_is_not_resolvable_from_chance_at_four_thousand_trials() -> None:
    """The statistics fact the page copy states, pinned as a computation."""
    row = next(item for item in figures.dimension_sweep() if item["d"] == 256)
    assert row["standard_error"] == pytest.approx(0.007904736566603367, abs=1e-12)
    assert row["resolvable_from_chance"] is False
    assert row["simple"] - 0.5 < 2.0 * row["standard_error"]


def test_sweep_legend_renders_the_ceiling_label_once() -> None:
    script = (
        "import * as mod from '%s';"
        "console.log(mod.renderSweep(mod.sweepModel()));"
    ) % SWEEP_JS.as_uri()
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    markup = completed.stdout
    assert markup.count(">THEORETICAL CEILING</text>") == 1


def test_smaller_dimensions_are_resolvable_and_1024_is_not() -> None:
    flags = {row["d"]: row["resolvable_from_chance"] for row in figures.dimension_sweep()}
    assert flags[2] is True
    assert flags[4] is True
    assert flags[16] is True
    assert flags[64] is True
    assert flags[256] is False
    assert flags[1024] is False


def test_sweep_never_surfaces_the_quarantined_printed_figure() -> None:
    for row in figures.dimension_sweep():
        for key in ("separable", "simple", "ceiling"):
            assert abs(row[key] - 0.5078125) > 1e-9
