"""Contracts for the hull, heat-map, and dimension-sweep figures.

Each fixture table in ui/hull.js, ui/heatmap.js, and ui/sweep.js is pinned here
against the kernel rather than trusted. The rendering rules from the design
contract are asserted on the markup, which is why the renderers return strings
instead of touching the DOM.

The honesty rules get the most attention in this file:

* the separable hull-nearest point is ANALYTIC and attained by the flagship circuit;
* the best-aligned heat-map curve must never score below the fixed-basis curve,
  and must agree with an independent brute-force search at a spot-checked point;
* the d=1024 sweep row must be labelled precomputed, and the d=256 row must
  carry the standard-error statistics fact.
"""

from __future__ import annotations

import json
import math
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from quantum import figures, science  # noqa: E402

HULL_JS = REPO_ROOT / "ui" / "hull.js"
HEATMAP_JS = REPO_ROOT / "ui" / "heatmap.js"
SWEEP_JS = REPO_ROOT / "ui" / "sweep.js"
MAIN_JS = REPO_ROOT / "main.js"
MAIN_CSS = REPO_ROOT / "main.css"
INDEX_HTML = REPO_ROOT / "index.html"

SWEEP_DIMENSIONS = [2, 4, 16, 64, 256, 1024]
CHANCE = 0.5
HISTORICAL_FIGURE = "0.5078125"


# ------------------------------------------------------------ node evaluation


def _run_node(module: Path, body: str) -> str:
    script = "const mod = await import('%s');\n" % module.as_uri() + body + "\n"
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return completed.stdout


def _node(module: Path, expression: str) -> list:
    """Evaluate `expression`, which pushes onto `result`, and return the array."""
    body = "const result = [];\n" + expression + "\nconsole.log(JSON.stringify(result));"
    return json.loads(_run_node(module, body))


def _node_json(module: Path, expression: str):
    """Evaluate `expression`, which must print one JSON value, and decode it."""
    return json.loads(_run_node(module, expression))


def _node_text(module: Path, expression: str) -> str:
    return _run_node(module, expression)


# ---------------------------------------------------------------- hull model


@pytest.fixture(scope="module")
def hull_model() -> dict:
    return _node_json(HULL_JS, "console.log(JSON.stringify(mod.hullModel()));")


@pytest.fixture(scope="module")
def hull_markup() -> str:
    return _node_text(
        HULL_JS, "console.log(mod.renderHull(mod.hullModel()));"
    )


def test_hull_fixture_dimension_matches_the_kernel() -> None:
    values = _node(HULL_JS, "result.push(mod.HULL_FIXTURE.dimension);")
    assert values[0] == figures.HULL_DIMENSION


def test_hull_fixture_eigenvalues_match_the_kernel_circle() -> None:
    """Each fixture point is a unit-modulus point with the kernel multiplicity."""
    fixture = _node(
        HULL_JS,
        "result.push(mod.HULL_FIXTURE.eigenvalues.map(function (p) {"
        " return [p.re, p.im, p.multiplicity]; }));",
    )[0]
    expected = figures.eigenvalue_circle(figures.HULL_DIMENSION)["points"]
    assert len(fixture) == len(expected)
    for point, kernel_point in zip(fixture, expected):
        assert point[0] == pytest.approx(kernel_point["re"], abs=1e-12)
        assert point[1] == pytest.approx(kernel_point["im"], abs=1e-12)
        assert point[2] == kernel_point["multiplicity"]


def test_hull_fixture_centroid_matches_the_kernel() -> None:
    values = _node(
        HULL_JS, "result.push([mod.HULL_FIXTURE.centroid.re, mod.HULL_FIXTURE.centroid.im]);"
    )
    centroid, _vertices = figures.hull_centroid_and_vertices(figures.HULL_DIMENSION)
    assert values[0][0] == pytest.approx(centroid["re"], abs=1e-12)
    assert values[0][1] == pytest.approx(centroid["im"], abs=1e-12)


def test_hull_fixture_vertices_match_the_kernel_in_angular_order() -> None:
    values = _node(
        HULL_JS, "result.push(mod.HULL_FIXTURE.hullVertices.map(function (v) { return [v.re, v.im]; }));"
    )[0]
    _centroid, vertices = figures.hull_centroid_and_vertices(figures.HULL_DIMENSION)
    assert len(values) == len(vertices)
    for point, vertex in zip(values, vertices):
        assert point[0] == pytest.approx(vertex["re"], abs=1e-12)
        assert point[1] == pytest.approx(vertex["im"], abs=1e-12)
    angles = [math.atan2(p[1], p[0]) % (2 * math.pi) for p in values]
    assert angles == sorted(angles)


def test_hull_model_recomputes_the_centroid_when_eigenvalues_move(hull_model: dict) -> None:
    """The centroid is a live computation, not a frozen fixture."""
    values = _node(
        HULL_JS,
        "var m = mod.hullModel({ eigenvalues: ["
        "  { re: 1, im: 0, angle: 0, multiplicity: 1 },"
        "  { re: -1, im: 0, angle: Math.PI, multiplicity: 1 }"
        " ], selected: 0 });"
        "result.push([m.centroid.re, m.centroid.im]);",
    )
    assert values[0][0] == pytest.approx(0.0, abs=1e-12)
    assert values[0][1] == pytest.approx(0.0, abs=1e-12)
    del hull_model


def test_hull_marks_the_centroid_as_an_attainable_analytic_point(hull_model: dict) -> None:
    centroid = hull_model["centroid"]
    assert centroid["kind"] == "ANALYTIC"
    assert centroid["token"] == "ANALYTIC"
    assert centroid["attainedByCircuit"] is True
    assert centroid["modulus"] == pytest.approx(abs(science.overlap(figures.HULL_DIMENSION)), abs=1e-12)


def test_hull_labels_the_separable_nearest_point_as_an_attained_analytic_value(
    hull_model: dict,
) -> None:
    """The hull point is attained by the shipped flagship separable strategy."""
    point = hull_model["separableNearest"]
    assert point["kind"] == "ANALYTIC"
    assert point["token"] == "ANALYTIC"
    assert point["attainedByCircuit"] is True
    assert point["modulus"] == pytest.approx(0.0, abs=1e-9)


def test_hull_marks_the_separable_point_attained(hull_model: dict) -> None:
    blob = json.dumps(hull_model)
    separable = json.dumps(hull_model["separableNearest"])
    assert '"attainedbycircuit":true' in separable.lower().replace(" ", "")
    assert separable.count("ANALYTIC") == 2
    assert blob.count("THEORETICAL_CEILING") == 0


def test_hull_eigenvalues_sit_on_the_unit_circle(hull_model: dict) -> None:
    for item in hull_model["eigenvalues"]:
        assert math.hypot(item["re"], item["im"]) == pytest.approx(1.0, abs=1e-12)


def test_hull_is_degenerate_at_the_flagship_spectrum(hull_model: dict) -> None:
    """{+1, -1 x 15} has a two-vertex hull: the whole diameter."""
    assert len(hull_model["hull"]) == 2


def test_hull_convex_hull_helper_reproduces_the_kernel_vertices() -> None:
    values = _node(
        HULL_JS,
        "var points = [{re: 1, im: 0}, {re: -1, im: 0}];"
        "result.push(mod.convexHull(points).map(function (v) { return [v.re, v.im]; }));",
    )[0]
    assert len(values) == 2
    for point in values:
        assert math.hypot(point[0], point[1]) == pytest.approx(1.0, abs=1e-12)


def test_hull_convex_hull_helper_drops_interior_points() -> None:
    values = _node(
        HULL_JS,
        "var points = [{re: 1, im: 1}, {re: -1, im: 1}, {re: -1, im: -1}, {re: 1, im: -1},"
        " {re: 0.2, im: 0.3}, {re: -0.4, im: 0.1}];"
        "var hull = mod.convexHull(points);"
        "result.push(hull.length);"
        "result.push(hull.map(function (v) { return [v.re, v.im]; }));",
    )
    assert values[0] == 4, "both interior points are dropped"
    assert sorted(values[1]) == sorted([[1.0, 1.0], [-1.0, 1.0], [-1.0, -1.0], [1.0, -1.0]])


def test_hull_convex_hull_helper_keeps_points_outside_the_diameter() -> None:
    """A point off the diameter is a hull vertex, not an interior point."""
    values = _node(
        HULL_JS,
        "var points = [{re: 1, im: 0}, {re: -1, im: 0}, {re: 0, im: -0.5}];"
        "var hull = mod.convexHull(points);"
        "result.push(hull.length);",
    )
    assert values[0] == 3


def test_hull_convex_hull_helper_terminates_on_collinear_points() -> None:
    values = _node(
        HULL_JS,
        "var hull = mod.convexHull([{re: -1, im: 0}, {re: 0, im: 0}, {re: 1, im: 0}]);"
        "result.push(hull.length);",
    )
    assert values[0] == 2, "a collinear set reduces to its two extreme points"


def test_hull_nearest_point_helper_finds_the_origin_on_an_edge() -> None:
    values = _node(
        HULL_JS,
        "var hull = [{re: 1, im: 0}, {re: -1, im: 0}];"
        "var point = mod.nearestPointToOrigin(hull);"
        "result.push([point.re, point.im, point.modulus]);",
    )[0]
    assert values[0] == pytest.approx(0.0, abs=1e-12)
    assert values[1] == pytest.approx(0.0, abs=1e-12)
    assert values[2] == pytest.approx(0.0, abs=1e-12)


# --------------------------------------------------------------- drag/keyboard


def test_drag_snaps_the_eigenvalue_onto_the_circle() -> None:
    values = _node(
        HULL_JS,
        "var moved = mod.moveEigenvalue(mod.HULL_FIXTURE.eigenvalues, 0, 1.0);"
        "result.push([moved[0].re, moved[0].im, Math.hypot(moved[0].re, moved[0].im)]);",
    )[0]
    assert values[2] == pytest.approx(1.0, abs=1e-12)
    assert values[0] == pytest.approx(math.cos(1.0), abs=1e-12)
    assert values[1] == pytest.approx(math.sin(1.0), abs=1e-12)


def test_drag_leaves_the_other_eigenvalues_untouched() -> None:
    values = _node(
        HULL_JS,
        "var before = mod.HULL_FIXTURE.eigenvalues;"
        "var moved = mod.moveEigenvalue(before, 0, 0.7);"
        "result.push([moved[1].re === before[1].re, moved[1].im === before[1].im]);",
    )[0]
    assert values == [True, True]


def test_keyboard_alternative_moves_the_selected_eigenvalue_along_the_circle() -> None:
    values = _node(
        HULL_JS,
        "var step = mod.HULL_FIXTURE.drag.step;"
        "var lo = mod.HULL_FIXTURE.drag.minAngle;"
        "var hi = mod.HULL_FIXTURE.drag.maxAngle;"
        "result.push(mod.angleFromKey('ArrowRight', 0));"
        "result.push(mod.angleFromKey('ArrowLeft', 0));"
        "result.push(mod.angleFromKey('ArrowRight', hi));"
        "result.push(mod.angleFromKey('ArrowLeft', lo));"
        "result.push(step);"
        "result.push(hi);"
        "result.push(lo);",
    )
    assert values[0] == pytest.approx(values[4], abs=1e-12)
    assert values[1] == pytest.approx(-values[4], abs=1e-12)
    assert values[2] == pytest.approx(values[5], abs=1e-12)
    assert values[3] == pytest.approx(values[6], abs=1e-12)
    assert values[4] == pytest.approx(math.radians(3.0), abs=1e-12)


def test_vertical_arrows_also_move_along_the_circle() -> None:
    values = _node(
        HULL_JS,
        "var step = mod.HULL_FIXTURE.drag.step;"
        "var lo = mod.HULL_FIXTURE.drag.minAngle;"
        "var hi = mod.HULL_FIXTURE.drag.maxAngle;"
        "result.push(mod.angleFromKey('ArrowUp', 0));"
        "result.push(mod.angleFromKey('ArrowDown', 0));"
        "result.push(mod.angleFromKey('ArrowUp', hi));"
        "result.push(mod.angleFromKey('ArrowDown', lo));"
        "result.push(step);"
        "result.push(hi);"
        "result.push(lo);",
    )
    assert values[0] == pytest.approx(values[4], abs=1e-12)
    assert values[1] == pytest.approx(-values[4], abs=1e-12)
    assert values[2] == pytest.approx(values[5], abs=1e-12)
    assert values[3] == pytest.approx(values[6], abs=1e-12)


def test_unrelated_keys_do_not_move_the_eigenvalue() -> None:
    values = _node(
        HULL_JS,
        "result.push([mod.angleFromKey('a', 0.4), mod.angleFromKey('Enter', 0.4),"
        " mod.angleFromKey('Tab', 0.4)]);",
    )[0]
    assert values == [0.4, 0.4, 0.4]


def test_angle_clamping_keeps_the_drag_inside_the_window() -> None:
    values = _node(
        HULL_JS,
        "result.push([mod.clampAngle(99), mod.clampAngle(-99)]);",
    )[0]
    drag = figures.__dict__  # noqa: F841  (kept for symmetry with the JS side)
    del drag
    assert values[0] == pytest.approx(math.pi, abs=1e-12)
    assert values[1] == pytest.approx(-math.pi, abs=1e-12)


def test_point_to_angle_inverts_angle_to_point() -> None:
    values = _node(
        HULL_JS,
        "var angle = 0.8;"
        "var point = mod.angleToPoint(angle);"
        "var recovered = mod.pointToAngle(point.x, point.y);"
        "result.push([point.x, point.y, recovered]);",
    )[0]
    assert values[2] == pytest.approx(0.8, abs=1e-3)


def test_point_to_angle_is_a_pure_direction_read() -> None:
    """Any point along the same ray from the centre gives the same angle."""
    values = _node(
        HULL_JS,
        "var near = mod.pointToAngle(240, 220);"
        "var far = mod.pointToAngle(250, 210);"
        "result.push([near, far, Math.atan2(10, 10)]);",
    )[0]
    assert values[0] == pytest.approx(values[2], abs=1e-12)
    assert values[1] == pytest.approx(values[2], abs=1e-12)


def test_keyboard_step_matches_the_three_degree_nudge() -> None:
    values = _node(HULL_JS, "result.push(mod.HULL_FIXTURE.drag.step);")
    assert values[0] == pytest.approx(math.radians(3.0), abs=1e-15)


# ------------------------------------------------------------- hull rendering


def test_hull_markup_is_an_image_with_a_usable_aria_label(hull_markup: str) -> None:
    assert 'role="img"' in hull_markup
    label = re.search(r'aria-label="([^"]*)"', hull_markup)
    assert label is not None
    text = label.group(1)
    assert "ANALYTIC" in text
    assert "THEORETICAL CEILING" not in text
    assert "attain this point" in text
    assert "arrow keys" in text
    assert "dimension 16" in text


def test_hull_markup_prints_the_kind_tag_next_to_each_point(hull_markup: str) -> None:
    assert 'data-kind="ANALYTIC"' in hull_markup
    assert 'data-kind="THEORETICAL_CEILING"' not in hull_markup
    assert ">ANALYTIC<" in hull_markup
    assert ">THEORETICAL CEILING<" not in hull_markup


def test_hull_separable_marker_has_its_own_shape(hull_markup: str) -> None:
    """Shape, not colour, distinguishes the two attained probe strategies."""
    bound = re.search(r'<g data-role="separable-bound".*?</g>', hull_markup, flags=re.S)
    assert bound is not None
    assert 'class="hv-bound"' in bound.group(0)
    centroid = re.search(r'<g data-role="centroid".*?</g>', hull_markup, flags=re.S)
    assert centroid is not None
    assert 'class="hv-centroid"' in centroid.group(0)


def test_hull_draws_only_lines_and_circles(hull_markup: str) -> None:
    for banned in ("<path", "<polyline", "<polygon", "<bezier"):
        assert banned not in hull_markup, f"thread-like geometry: {banned}"
    assert "<line" in hull_markup
    assert "<circle" in hull_markup


def test_hull_declares_no_animation(hull_markup: str) -> None:
    for banned in ("<animate", "<animateTransform", "<set", "animateMotion", "transition"):
        assert banned not in hull_markup


def test_hull_uses_a_fixed_viewbox_and_pixel_strokes(hull_markup: str) -> None:
    assert 'viewBox="0 0 460 460"' in hull_markup
    assert "preserveAspectRatio" in hull_markup
    assert re.search(r'stroke-width="1"', hull_markup)
    assert "vector-effect" not in hull_markup


def test_hull_never_surfaces_the_quarantined_printed_figure() -> None:
    for path in (HULL_JS, HEATMAP_JS, SWEEP_JS):
        text = path.read_text(encoding="utf-8")
        assert HISTORICAL_FIGURE not in text
        assert "5078125" not in text


# ------------------------------------------------------------- heat map data


def test_heatmap_fixed_basis_fixture_matches_the_kernel() -> None:
    values = _node(
        HEATMAP_JS,
        "result.push(mod.HEATMAP_FIXTURE.fixedBasis.map(function (p) {"
        " return [p.entropy, p.lambda, p.success]; }));",
    )[0]
    assert len(values) == 5
    for entropy, lambda_0, success in values:
        row = figures.fixed_basis_curve(entropy, 2)
        assert lambda_0 == pytest.approx(row["lambda_0"], abs=5e-5)
        assert success == pytest.approx(row["success"], abs=5e-5)


def test_heatmap_best_aligned_fixture_matches_the_kernel() -> None:
    values = _node(
        HEATMAP_JS,
        "result.push(mod.HEATMAP_FIXTURE.bestAligned.map(function (p) {"
        " return [p.entropy, p.lambda, p.success]; }));",
    )[0]
    assert len(values) == 5
    for entropy, lambda_0, success in values:
        row = figures.best_aligned_curve(entropy, 2)
        assert lambda_0 == pytest.approx(row["lambda_0"], abs=5e-5)
        assert success == pytest.approx(row["success"], abs=5e-5)


def test_heatmap_best_aligned_never_scores_below_fixed_basis() -> None:
    """The requirement, asserted on the shipped fixtures."""
    values = _node(
        HEATMAP_JS,
        "var f = mod.HEATMAP_FIXTURE.fixedBasis;"
        "var a = mod.HEATMAP_FIXTURE.bestAligned;"
        "var out = [];"
        "for (var i = 0; i < f.length; i += 1) { out.push(a[i].success >= f[i].success - 1e-12); }"
        "result.push(out);",
    )[0]
    assert all(values), "best-aligned dipped below fixed-basis at some point"


def test_heatmap_entropy_points_match_the_kernel() -> None:
    values = _node(HEATMAP_JS, "result.push(mod.HEATMAP_FIXTURE.entropyPoints);")
    assert values[0] == [0, 0.25, 0.5, 0.75, 1]


def test_heatmap_reports_best_aligned_as_present() -> None:
    values = _node(HEATMAP_JS, "result.push([mod.bestAlignedPresent(), mod.heatmapModel().bestAlignedPresent]);")
    assert values[0] == [True, True]
    assert figures.unverified_heatmap_present() is False


def test_heatmap_success_values_come_from_the_kernel() -> None:
    values = _node(
        HEATMAP_JS,
        "var out = [];"
        "mod.heatmapModel().bestAligned.forEach(function (p) { out.push(p.success); });"
        "result.push(out);",
    )[0]
    for success in values:
        assert 0.5 <= success <= 1.0


# --------------------------------------------------------- heat map rendering


@pytest.fixture(scope="module")
def heatmap_model() -> dict:
    return _node_json(HEATMAP_JS, "console.log(JSON.stringify(mod.heatmapModel()));")


@pytest.fixture(scope="module")
def heatmap_markup() -> str:
    return _node_text(HEATMAP_JS, "console.log(mod.renderHeatmap(mod.heatmapModel()));")


def test_heatmap_model_carries_both_curves(heatmap_model: dict) -> None:
    assert len(heatmap_model["fixedBasis"]) == 5
    assert len(heatmap_model["bestAligned"]) == 5
    assert heatmap_model["bestAlignedPresent"] is True


def test_heatmap_labels_every_point_as_a_bound(heatmap_model: dict) -> None:
    for curve in ("fixedBasis", "bestAligned"):
        for point in heatmap_model[curve]:
            assert point["kind"] == "THEORETICAL CEILING"
            assert point["token"] == "THEORETICAL_CEILING"


def test_heatmap_points_lie_inside_the_success_axis(heatmap_model: dict) -> None:
    for curve in ("fixedBasis", "bestAligned"):
        for point in heatmap_model[curve]:
            assert 0.5 <= point["success"] <= 1.0
            assert heatmap_model["layout"]["plotTop"] <= point["y"] <= heatmap_model["layout"]["plotBottom"]


def test_heatmap_axes_are_labelled(heatmap_model: dict) -> None:
    assert heatmap_model["axes"]["lambda"]["label"] == "OVERLAP LAMBDA_0"
    assert heatmap_model["axes"]["entropy"]["label"] == "ENTANGLEMENT ENTROPY (BITS)"
    assert heatmap_model["axes"]["success"]["label"] == "ONE-QUERY WIN PROBABILITY"


def test_heatmap_markup_is_an_image_with_a_usable_aria_label(heatmap_markup: str) -> None:
    assert 'role="img"' in heatmap_markup
    label = re.search(r'aria-label="([^"]*)"', heatmap_markup)
    assert label is not None
    text = label.group(1)
    assert "fixed-basis" in text
    assert "best-aligned" in text
    assert "theoretical ceilings" in text
    assert "neither is measured" in text


def test_heatmap_markup_labels_both_curves_as_ceilings(heatmap_markup: str) -> None:
    assert 'data-role="fixed-basis"' in heatmap_markup
    assert 'data-role="best-aligned"' in heatmap_markup
    assert 'data-kind="THEORETICAL_CEILING"' in heatmap_markup
    assert heatmap_markup.count('data-kind="THEORETICAL_CEILING"') == 10


def test_heatmap_legend_states_that_neither_curve_is_measured(heatmap_markup: str) -> None:
    assert "NEITHER IS A MEASUREMENT" in heatmap_markup
    assert "THEORETICAL CEILING" in heatmap_markup


def test_heatmap_draws_the_chance_line_at_one_half(heatmap_markup: str) -> None:
    assert 'data-role="chance-line"' in heatmap_markup
    assert "CHANCE 1/2" in heatmap_markup


def test_heatmap_declares_no_motion_and_no_thread_geometry(heatmap_markup: str) -> None:
    for banned in ("<path", "<polyline", "<polygon", "<animate", "<set", "transition"):
        assert banned not in heatmap_markup


def test_heatmap_uses_a_fixed_viewbox(heatmap_markup: str) -> None:
    assert 'viewBox="0 0 680 490"' in heatmap_markup
    assert "preserveAspectRatio" in heatmap_markup
    assert re.search(r'stroke-width="1"', heatmap_markup)


def test_heatmap_text_equivalent_reports_both_curves() -> None:
    values = _node(
        HEATMAP_JS,
        "var rows = mod.heatmapTextEquivalent(mod.heatmapModel());"
        "result.push(rows.length);"
        "result.push(rows[0].text);",
    )
    assert values[0] == 10
    assert "THEORETICAL CEILING" in values[1]
    assert "LAMBDA_0" in values[1]


def test_heatmap_text_equivalent_would_say_unverified_without_the_curve() -> None:
    values = _node(
        HEATMAP_JS,
        "var model = mod.heatmapModel();"
        "model.bestAligned = [];"
        "model.bestAlignedPresent = false;"
        "var markup = mod.renderHeatmap(model);"
        "var rows = mod.heatmapTextEquivalent(model);"
        "result.push([markup.indexOf('UNVERIFIED') !== -1,"
        " rows.some(function (r) { return r.text.indexOf('UNVERIFIED') !== -1; })]);",
    )[0]
    assert values == [True, True], "the fallback must label the curve UNVERIFIED"


# ------------------------------------------------------------- sweep fixture


def test_sweep_fixture_covers_exactly_the_requested_dimensions() -> None:
    values = _node(
        SWEEP_JS, "result.push(mod.SWEEP_FIXTURE.rows.map(function (r) { return r.d; }));"
    )[0]
    assert values == SWEEP_DIMENSIONS


@pytest.mark.parametrize("d", SWEEP_DIMENSIONS)
def test_sweep_fixture_values_match_the_kernel(d: int) -> None:
    values = _node(
        SWEEP_JS,
        "var row = mod.SWEEP_FIXTURE.rows.filter(function (r) { return r.d === %d; })[0];"
        "result.push([row.separable, row.simple, row.ceiling,"
        " row.standardError, row.resolvableFromChance, row.source]);" % d,
    )[0]
    assert values[0] == science.SEPARABLE_SUCCESS
    assert values[1] == science.simple_success(d)
    assert values[2] == pytest.approx(science.helstrom_ceiling(d), abs=1e-15)
    assert values[3] == pytest.approx(
        math.sqrt(science.simple_success(d) * (1 - science.simple_success(d)) / 4000), abs=1e-15
    )
    expected_source = "PRECOMPUTED" if d > 256 else "LIVE_KERNEL"
    assert values[5] == expected_source


def test_sweep_separable_curve_is_flat_at_one() -> None:
    values = _node(
        SWEEP_JS, "result.push(mod.SWEEP_FIXTURE.rows.map(function (r) { return r.separable; }));"
    )[0]
    assert set(values) == {1.0}


def test_sweep_labels_the_1024_row_precomputed_and_the_rest_live() -> None:
    values = _node(
        SWEEP_JS,
        "result.push(mod.SWEEP_FIXTURE.rows.map(function (r) {"
        " return [r.d, r.live, r.source]; }));",
    )[0]
    for d, live, source in values:
        if d == 1024:
            assert live is False
            assert source == "PRECOMPUTED"
        else:
            assert live is True
            assert source == "LIVE_KERNEL"


def test_sweep_carries_the_256_statistics_fact() -> None:
    values = _node(
        SWEEP_JS,
        "var row = mod.SWEEP_FIXTURE.rows.filter(function (r) { return r.d === 256; })[0];"
        "result.push([row.standardError, row.resolvableFromChance, row.simple]);",
    )[0]
    assert values[0] == pytest.approx(0.007904736566603367, abs=1e-15)
    assert values[1] is False
    assert values[2] - 0.5 < 2 * values[0]


def test_sweep_carries_the_resolvability_flag_for_every_dimension() -> None:
    values = _node(
        SWEEP_JS,
        "result.push(mod.SWEEP_FIXTURE.rows.map(function (r) { return r.resolvableFromChance; }));",
    )[0]
    assert values == [True, True, True, True, False, False]


# ----------------------------------------------------------- sweep rendering


@pytest.fixture(scope="module")
def sweep_model() -> dict:
    return _node_json(SWEEP_JS, "console.log(JSON.stringify(mod.sweepModel()));")


@pytest.fixture(scope="module")
def sweep_markup() -> str:
    return _node_text(SWEEP_JS, "console.log(mod.renderSweep(mod.sweepModel()));")


def test_sweep_model_labels_every_value_kind(sweep_model: dict) -> None:
    for row in sweep_model["rows"]:
        assert row["separableKind"] == "ANALYTIC"
        assert row["simpleKind"] == "ANALYTIC"
        assert row["ceilingKind"] == "THEORETICAL CEILING"
        assert row["separableToken"] == "ANALYTIC"
        assert row["simpleToken"] == "ANALYTIC"
        assert row["ceilingToken"] == "THEORETICAL_CEILING"


def test_sweep_columns_are_ordered_by_dimension(sweep_model: dict) -> None:
    assert [row["d"] for row in sweep_model["rows"]] == SWEEP_DIMENSIONS
    xs = [row["x"] for row in sweep_model["rows"]]
    assert xs == sorted(xs)


def test_sweep_executable_curve_falls_toward_chance(sweep_model: dict) -> None:
    values = [row["simple"] for row in sweep_model["rows"]]
    assert values == sorted(values, reverse=True)
    assert values[-1] > 0.5


def test_sweep_ceiling_stays_above_the_executable_value(sweep_model: dict) -> None:
    for row in sweep_model["rows"]:
        assert row["ceiling"] >= row["simple"]
        assert row["ceilingY"] <= row["simpleY"]


def test_sweep_markup_is_an_image_with_a_usable_aria_label(sweep_markup: str) -> None:
    assert 'role="img"' in sweep_markup
    label = re.search(r'aria-label="([^"]*)"', sweep_markup)
    assert label is not None
    text = label.group(1)
    assert "2, 4, 16, 64, 256 and 1024" in text
    assert "precomputed and never executed" in text
    assert "none is measured" in text


def test_sweep_markup_prints_kind_tags_on_every_value(sweep_markup: str) -> None:
    assert 'data-kind="ANALYTIC"' in sweep_markup
    assert 'data-kind="THEORETICAL_CEILING"' in sweep_markup
    assert ">ANALYTIC<" in sweep_markup
    assert "THEORETICAL CEILING" in sweep_markup


def test_sweep_marks_the_1024_column_precomputed(sweep_markup: str) -> None:
    assert ">PRECOMPUTED<" in sweep_markup
    assert 'data-source="PRECOMPUTED"' in sweep_markup
    assert "theory only, never executed" in sweep_markup


def test_sweep_annotates_the_unresolvable_dimension(sweep_markup: str) -> None:
    assert "BELOW CHANCE RESOLUTION" in sweep_markup
    assert 'data-role="resolution-marker"' in sweep_markup


def test_sweep_draws_the_chance_line(sweep_markup: str) -> None:
    assert 'data-role="chance-line"' in sweep_markup
    assert "CHANCE 1/2" in sweep_markup


def test_sweep_declares_no_motion_and_no_thread_geometry(sweep_markup: str) -> None:
    for banned in ("<path", "<polyline", "<polygon", "<animate", "<set", "transition"):
        assert banned not in sweep_markup


def test_sweep_uses_a_fixed_viewbox(sweep_markup: str) -> None:
    assert 'viewBox="0 0 760 480"' in sweep_markup
    assert re.search(r'stroke-width="1"', sweep_markup)


def test_figure_coordinates_are_finite(hull_markup: str, heatmap_markup: str, sweep_markup: str) -> None:
    """Missing point fields and missing chance values must never reach SVG."""
    for markup in (hull_markup, heatmap_markup, sweep_markup):
        coordinates = re.findall(r'\b(?:x|y|x1|y1|x2|y2|cx|cy)="([^"]+)"', markup)
        assert coordinates
        assert all(math.isfinite(float(value)) for value in coordinates)


def test_sweep_marks_fit_inside_plot(sweep_model: dict) -> None:
    layout = sweep_model["layout"]
    for row in sweep_model["rows"]:
        assert layout["axisLeft"] <= row["x"] - 22
        assert row["x"] + 22 <= layout["axisRight"]


def test_sweep_text_equivalent_states_the_statistics_facts() -> None:
    values = _node(
        SWEEP_JS,
        "var rows = mod.sweepTextEquivalent(mod.sweepModel());"
        "result.push(rows.length);"
        "result.push(rows[4].text);"
        "result.push(rows[5].text);",
    )
    assert values[0] == 6
    assert "STANDARD ERROR AT 4000 TRIALS 0.007904736566603367" in values[1]
    assert "NOT RESOLVABLE FROM CHANCE" in values[1]
    assert "PRECOMPUTED, THEORY ONLY, NEVER EXECUTED" in values[2]


# -------------------------------------------------------------- page wiring


def test_index_html_mounts_all_three_proof_figures() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")
    for host in ("sweep", "hull", "heatmap"):
        assert f'id="{host}"' in html
    for ledger in ("sweep-values", "hull-values", "heatmap-values"):
        assert f'id="{ledger}"' in html
    assert html.count("<figcaption") >= 4


def test_main_js_mounts_each_figure_exactly_once() -> None:
    source = MAIN_JS.read_text(encoding="utf-8")
    assert source.count("mountSweep(") == 1
    assert source.count("mountHullView(") == 1
    assert source.count("mountHeatmap(") == 1
    assert "ui/hull.js" in source
    assert "ui/heatmap.js" in source
    assert "ui/sweep.js" in source


def test_the_new_figures_make_no_bridge_call() -> None:
    source = MAIN_JS.read_text(encoding="utf-8")
    code = re.sub(r"/\*.*?\*/", " ", source, flags=re.S)
    for host in ("sweep", "hull", "heatmap"):
        assert f'callBridge("get_' not in code.split(host)[0][-200:]
    assert code.count('callBridge("get_experience"') == 1
    assert code.count('callBridge("get_gallery"') == 1


def test_hull_host_is_reachable_by_keyboard() -> None:
    """The arrow-key alternative needs a focusable host with a label."""
    source = MAIN_JS.read_text(encoding="utf-8")
    assert 'hullHost.setAttribute("tabindex", "0")' in source
    assert 'hullHost.setAttribute("aria-label"' in source
    assert "Arrow keys" in source or "arrow keys" in source


def test_touched_javascript_parses_as_an_es_module() -> None:
    for path in (HULL_JS, HEATMAP_JS, SWEEP_JS, MAIN_JS):
        completed = subprocess.run(
            ["node", "--check", str(path)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            check=False,
        )
        assert completed.returncode == 0, f"{path.name}: {completed.stderr}"


def test_new_figure_rules_stay_inside_the_motion_budget() -> None:
    css = MAIN_CSS.read_text(encoding="utf-8")
    root = re.search(r":root\s*\{.*?\n\}", css, flags=re.S)
    assert root is not None
    rules = css[: root.start()] + css[root.end() :]
    lowered = rules.lower()
    for banned in ("@keyframes", "animation", "transition", "infinite"):
        assert banned not in lowered
    durations = set(re.findall(r"(\d+)ms", lowered))
    assert durations <= {"0", "80", "140", "220"}


def test_new_figure_rules_use_tokens_and_zero_radius() -> None:
    css = MAIN_CSS.read_text(encoding="utf-8")
    root = re.search(r":root\s*\{.*?\n\}", css, flags=re.S)
    assert root is not None
    rules = css[: root.start()] + css[root.end() :]
    for selector in (".hullview", ".hv-eigenvalue", ".hv-bound", ".sw-mark", ".sw-separable"):
        block = re.search(re.escape(selector) + r"(?:\[[^\]]*\])?\s*\{([^}]*)\}", rules)
        assert block is not None, f"{selector} rule is missing from main.css"
    for match in re.finditer(r"border-radius:\s*([^;]+);", rules):
        assert match.group(1).strip() in ("0", "0px")
    assert not re.search(r"#[0-9a-fA-F]{3,6}\b", rules)


@pytest.mark.parametrize(
    "word",
    [
        "strand",
        "filament",
        "fibre",
        "fiber",
        "slack",
        "fray",
        "unravel",
        "weaker entanglement",
        "decaying entanglement",
        "fading",
        "dying",
        "loosening",
        "particles",
        "wavelength",
    ],
)
def test_no_decay_metaphor_in_the_new_figures_or_the_page(word: str) -> None:
    for path in (HULL_JS, HEATMAP_JS, SWEEP_JS, INDEX_HTML, MAIN_CSS):
        assert word not in path.read_text(encoding="utf-8").lower(), (
            f"{path.name} contains decay language: {word!r}"
        )


@pytest.mark.parametrize("path", [HULL_JS, HEATMAP_JS, SWEEP_JS])
def test_new_figure_sources_avoid_novelty_language(path: Path) -> None:
    lowered = path.read_text(encoding="utf-8").lower()
    for phrase in ("we discovered", "quantum advantage", "breakthrough", "new theorem"):
        assert phrase not in lowered


def test_no_three_js_or_animation_library_is_imported() -> None:
    for path in (HULL_JS, HEATMAP_JS, SWEEP_JS, MAIN_JS, INDEX_HTML):
        text = path.read_text(encoding="utf-8")
        for banned in ("three", "gsap", "anime.js", "d3", "http://", "https://", "@import"):
            assert banned not in text.lower(), f"{path.name} references {banned!r}"
