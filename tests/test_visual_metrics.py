"""Metric and rendering tests for the visual-science fingerprint figure.

Every number the figure prints is a kernel fixture, so the fixtures in
`ui/fingerprint.js` are pinned here against `quantum.science` rather than
trusted. Rendering rules from the design contract are asserted on the markup
the renderer produces, which is why the renderer returns a string instead of
touching the DOM.
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

from quantum.science import (  # noqa: E402
    GOLDEN_DIMENSIONS,
    SEPARABLE_SUCCESS,
    helstrom_ceiling,
    overlap,
    simple_success,
)

FINGERPRINT_JS = REPO_ROOT / "ui/fingerprint.js"
MAIN_CSS = REPO_ROOT / "main.css"
# Qollab loads only the root stylesheet, so the figure rules live in main.css.
FINGERPRINT_CSS = MAIN_CSS
INDEX_HTML = REPO_ROOT / "index.html"
MAIN_JS = REPO_ROOT / "main.js"

DIMENSIONS = [4, 16, 64, 256]
CHANCE = 0.5
HISTORICAL_FIGURE = "0.5078125"


def trace_distance(d: int) -> float:
    """Trace distance of the two channel outputs for the max-entanglement probe."""
    value = overlap(d)
    return math.sqrt(1.0 - value * value)


# ------------------------------------------------------------ node evaluation


def _node(expression: str, prelude: str = "") -> list:
    module_url = FINGERPRINT_JS.as_uri()
    script = (
        "const fp = await import('%s');\n" % module_url
        + prelude
        + "const result = [];\n"
        + expression
        + "\nconsole.log(JSON.stringify(result));\n"
    )
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


def _model() -> dict:
    script = (
        "const fp = await import('%s');\n" % FINGERPRINT_JS.as_uri()
        + "console.log(JSON.stringify(fp.figureModel()));\n"
    )
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


@pytest.fixture(scope="module")
def model() -> dict:
    return _model()


@pytest.fixture(scope="module")
def markup() -> str:
    script = (
        "const fp = await import('%s');\n" % FINGERPRINT_JS.as_uri()
        + "console.log(fp.renderFingerprint(fp.figureModel()));\n"
    )
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return completed.stdout


# ------------------------------------------------------- kernel-pinned metrics


@pytest.mark.parametrize("d", DIMENSIONS)
def test_signed_overlap_fixture_matches_the_kernel(d: int) -> None:
    values = _node("result.push(fp.METRICS[%d].overlap);" % d)
    assert values[0] == overlap(d)


@pytest.mark.parametrize("d", DIMENSIONS)
def test_trace_distance_fixture_matches_the_kernel(d: int) -> None:
    values = _node("result.push(fp.METRICS[%d].traceDistance);" % d)
    assert values[0] == pytest.approx(trace_distance(d), abs=1e-15)


@pytest.mark.parametrize("d", DIMENSIONS)
def test_executable_success_fixture_matches_the_kernel(d: int) -> None:
    values = _node("result.push(fp.METRICS[%d].executable);" % d)
    assert values[0] == simple_success(d)


@pytest.mark.parametrize("d", DIMENSIONS)
def test_ceiling_fixture_matches_the_kernel(d: int) -> None:
    values = _node("result.push(fp.METRICS[%d].ceiling);" % d)
    assert values[0] == helstrom_ceiling(d)


def test_metric_table_covers_exactly_the_golden_dimensions() -> None:
    keys = _node("result.push(Object.keys(fp.METRICS).map(Number).sort(function(a,b){return a-b;}));")
    assert keys[0] == list(GOLDEN_DIMENSIONS) == DIMENSIONS
    assert _node("result.push(fp.DIMENSIONS);")[0] == DIMENSIONS


def test_metric_table_carries_no_other_dimension() -> None:
    keys = _node("result.push(Object.keys(fp.METRICS).length);")
    assert keys[0] == 4


def test_historical_printed_figure_never_surfaces() -> None:
    text = FINGERPRINT_JS.read_text(encoding="utf-8")
    assert HISTORICAL_FIGURE not in text
    assert "5078125" not in text
    assert "507781982421875" in text, "the formula value is the one shown"


# --------------------------------------------------------------- metric trends


def test_absolute_overlap_increases_with_d() -> None:
    absolutes = _node(
        "fp.DIMENSIONS.forEach(function (d) { result.push(Math.abs(fp.METRICS[d].overlap)); });"
    )
    assert absolutes == sorted(absolutes)
    assert absolutes[-1] > absolutes[0]
    assert absolutes[-1] == pytest.approx(0.9921875, abs=1e-12)


def test_signed_overlap_approaches_minus_one_with_d() -> None:
    signed = _node(
        "fp.DIMENSIONS.forEach(function (d) { result.push(fp.METRICS[d].overlap); });"
    )
    assert signed == sorted(signed, reverse=True)
    assert signed[-1] == pytest.approx(-0.9921875, abs=1e-12)


def test_trace_distance_decreases_with_d() -> None:
    values = _node(
        "fp.DIMENSIONS.forEach(function (d) { result.push(fp.METRICS[d].traceDistance); });"
    )
    assert values == sorted(values, reverse=True)
    assert values[-1] == pytest.approx(0.12475562048961962, abs=1e-12)


def test_executable_success_approaches_the_chance_line() -> None:
    values = _node(
        "fp.DIMENSIONS.forEach(function (d) { result.push(fp.METRICS[d].executable); });"
    )
    assert all(value > CHANCE for value in values)
    assert values == sorted(values, reverse=True)
    assert values[-1] == pytest.approx(simple_success(256), abs=1e-12)


def test_ceiling_is_above_the_executable_value_and_also_falls_to_chance() -> None:
    gaps = _node(
        "fp.DIMENSIONS.forEach(function (d) {"
        " result.push([fp.METRICS[d].ceiling, fp.METRICS[d].executable]); });"
    )
    for ceiling, executable in gaps:
        assert ceiling > executable
        assert executable > CHANCE
    assert [pair[0] for pair in gaps] == sorted([pair[0] for pair in gaps], reverse=True)


def test_separable_stays_perfect_and_outside_the_figure_metrics() -> None:
    assert SEPARABLE_SUCCESS == 1.0
    assert not re.search(r"separable", FINGERPRINT_JS.read_text(encoding="utf-8"), re.I)


# -------------------------------------------------------------- axis contracts


def test_overlap_axis_is_signed_minus_one_to_one_and_labelled() -> None:
    values = _node(
        "result.push(fp.OVERLAP_AXIS.min);"
        "result.push(fp.OVERLAP_AXIS.max);"
        "result.push(fp.OVERLAP_AXIS.label);"
    )
    assert values[0] == -1
    assert values[1] == 1
    assert values[2] == "OVERLAP (SIGNED)"


def test_trace_distance_axis_is_zero_to_one() -> None:
    values = _node(
        "result.push(fp.TRACE_AXIS.min);"
        "result.push(fp.TRACE_AXIS.max);"
        "result.push(fp.TRACE_AXIS.label);"
    )
    assert values[0] == 0
    assert values[1] == 1
    assert values[2] == "TRACE DISTANCE"


def test_chance_line_is_one_half_and_drawn_as_a_reference() -> None:
    values = _node("result.push(fp.SUCCESS_AXIS.chance);result.push(fp.SUCCESS_AXIS.chanceLabel);")
    assert values == [0.5, "CHANCE 1/2"]


def test_model_places_overlap_marks_inside_the_signed_domain(model: dict) -> None:
    for row in model["rows"]:
        assert row["columnX"] <= row["overlapMarkX"] <= row["columnX"] + model["overlapWidth"]
    offsets = [row["overlapMarkX"] - row["columnX"] for row in model["rows"]]
    assert offsets == sorted(offsets, reverse=True), (
        "within its column the mark walks toward minus one"
    )


def test_output_state_marks_converge_with_d(model: dict) -> None:
    separations = [row["traceSeparationPx"] for row in model["rows"]]
    assert separations == sorted(separations, reverse=True)
    assert separations[-1] < separations[0]
    # the max-entanglement pair approaches the chance line as d grows
    for row in model["rows"]:
        assert row["traceDistance"] == pytest.approx(
            row["traceSeparationPx"] / model["traceWidth"], abs=1e-3
        )


# --------------------------------------------------- entanglement stays MAXIMAL


def test_entanglement_lock_is_maximal_for_every_dimension(model: dict) -> None:
    assert model["lock"]["label"] == "MAXIMAL"
    assert model["lock"]["heading"] == "ENTANGLEMENT"
    assert model["lock"]["dimensionDependent"] is False
    assert model["lock"]["scale"] is None
    assert model["lock"]["percent"] is None


def test_lock_geometry_is_identical_across_dimensions() -> None:
    geometry = _node(
        "var out = [];"
        "fp.DIMENSIONS.forEach(function (d) {"
        " var m = fp.figureModel();"
        " out.push(JSON.stringify([m.lock.cx, m.lock.cy, m.lock.r,"
        " m.lock.textX, m.lock.textY])); });"
        "result.push(out.every(function (v) { return v === out[0]; }));"
    )
    assert geometry == [True]


def test_lock_is_drawn_once_and_carries_no_bar_or_meter(markup: str) -> None:
    assert markup.count('data-role="entanglement-lock"') == 1
    assert "<meter" not in markup
    assert "<progress" not in markup
    lock = re.search(r'<g data-role="entanglement-lock".*?</g>', markup, flags=re.S)
    assert lock is not None
    assert "MAXIMAL" in lock.group(0)
    assert "<rect" not in lock.group(0), "the lock is not a track"


def test_lock_does_not_respond_to_dimension_in_markup(markup: str) -> None:
    lock = re.search(r'<g data-role="entanglement-lock".*?</g>', markup, flags=re.S)
    assert lock is not None
    assert "transition" not in lock.group(0)
    assert "animate" not in lock.group(0)


# ------------------------------------------------------------ kind tags as text


def test_every_metric_label_carries_its_kind_tag_as_text(model: dict) -> None:
    for row in model["rows"]:
        assert row["overlapKind"] == "ANALYTIC"
        assert row["traceKind"] == "ANALYTIC"
        assert row["executableKind"] == "ANALYTIC"
        assert row["ceilingKind"] == "THEORETICAL CEILING"


def test_chart_omits_dense_value_labels_and_keeps_kind_metadata(markup: str) -> None:
    # Dense exact readings live in the visible text ledger below the chart.
    # The SVG keeps marks and dimension labels legible at narrow widths.
    assert 'class="fp-kind"' not in markup
    assert 'class="fp-value"' not in markup
    assert markup.count('data-kind="ANALYTIC"') == len(DIMENSIONS) * 3
    assert markup.count('data-kind="THEORETICAL_CEILING"') == len(DIMENSIONS)
    assert ">THEORETICAL CEILING<" not in markup
    # Exact values remain in the SVG aria-label and visible ledger; they are
    # intentionally omitted as overlapping decorative text elements.
    assert "EMPIRICAL" in markup, "the figure states that no value here is measured"


def test_figure_states_that_measured_values_live_elsewhere(markup: str) -> None:
    assert "NOT MEASURED" in markup or "not measured" in markup


def test_measured_values_are_never_mixed_into_the_reference_marks(markup: str) -> None:
    """Reference marks are hairlines and ticks, never filled tracks."""
    for row in re.findall(r'<g data-role="success-row".*?</g>', markup, flags=re.S):
        assert 'data-kind="THEORETICAL_CEILING"' in row
        assert "<rect" not in row, "no filled track behind a reference value"


def test_analytic_and_ceiling_marks_are_distinct_and_labelled(markup: str) -> None:
    assert 'data-role="analytic-mark"' in markup
    assert 'data-role="ceiling-mark"' in markup
    assert 'data-role="chance-line"' in markup


def test_figure_model_keeps_empirical_out_of_the_fixture_figure(model: dict) -> None:
    blob = json.dumps(model)
    assert "EMPIRICAL" in blob, "the model states that nothing here is measured"
    assert model["measured"] is None
    for row in model["rows"]:
        assert row["measuredHere"] is False
        assert row["empiricalToken"] == "EMPIRICAL"


# ----------------------------------------------------------- text equivalent


def test_figure_has_a_text_equivalent_with_one_row_per_dimension() -> None:
    lines = _node(
        "var model = fp.figureModel();"
        "result.push(fp.textEquivalent(model).length);"
        "result.push(fp.textEquivalent(model)[0].label);"
    )
    assert lines[0] == len(DIMENSIONS)
    assert "d=4" in lines[1]


def test_text_equivalent_prints_the_kernel_values_with_kind_tags() -> None:
    line = _node(
        "var model = fp.figureModel();"
        "result.push(fp.textEquivalent(model)[3].text);"
    )
    text = line[0]
    assert "OVERLAP (SIGNED)" in text
    assert "ANALYTIC" in text
    assert "THEORETICAL CEILING" in text
    assert "-0.9921875" in text
    assert "0.507781982421875" in text
    assert "0.5623778102448098" in text
    assert HISTORICAL_FIGURE not in text


def test_text_equivalent_is_consistent_with_the_svg_markup() -> None:
    same = _node(
        "var model = fp.figureModel();"
        "var svg = fp.renderFingerprint(model);"
        "var rows = fp.textEquivalent(model);"
        "result.push(rows.every(function (row) { return svg.indexOf(row.label) !== -1; }));"
    )
    assert same == [True]


def test_markdown_ledger_rows_are_definition_list_pairs() -> None:
    entries = _node(
        "var model = fp.figureModel();"
        "result.push(fp.textEquivalent(model).map(function (r) {"
        " return [r.label, r.text]; }));"
    )
    for label, text in entries[0]:
        assert isinstance(label, str) and label
        assert isinstance(text, str) and text


# --------------------------------------------------------- figure accessibility


def test_svg_is_an_image_with_a_complete_aria_label(markup: str) -> None:
    assert 'role="img"' in markup
    label = re.search(r'aria-label="([^"]*)"', markup)
    assert label is not None
    text = label.group(1)
    for phrase in ("MAXIMAL", "OVERLAP (SIGNED)", "TRACE DISTANCE"):
        assert phrase in text
    for d in DIMENSIONS:
        assert f"d={d}" in text


def test_decorative_groups_are_hidden_from_assistive_technology(markup: str) -> None:
    groups = re.findall(r"<g\b[^>]*>", markup)
    assert groups
    for group in groups:
        assert 'aria-hidden="true"' in group or 'data-role=' in group
    assert markup.count('aria-hidden="true"') >= len(groups) - 1


def test_svg_uses_a_fixed_viewbox_and_pixel_strokes(markup: str) -> None:
    assert 'viewBox="0 0 760 420"' in markup
    assert "preserveAspectRatio" in markup
    assert re.search(r'stroke-width="1"', markup)
    assert "vector-effect" not in markup, "strokes are already declared in pixels"


def test_svg_has_no_transform_rotation_or_perspective(markup: str) -> None:
    assert 'transform="rotate' not in markup
    assert "perspective" not in markup.lower()
    assert "skew" not in markup.lower()


# ------------------------------------------------------------- no decay trope


def test_science_region_has_no_thread_like_geometry(markup: str) -> None:
    for banned in ("<path", "<polyline", "<polygon", "<bezier"):
        assert banned not in markup, f"thread-like geometry in the figure: {banned}"
    assert "<line" in markup and "<circle" in markup


def test_svg_declares_no_animation_element(markup: str) -> None:
    for banned in ("<animate", "<animateTransform", "<set", "animateMotion"):
        assert banned not in markup


def _figure_rules() -> str:
    """The figure block of the single shipped stylesheet, minus the token root."""
    css = MAIN_CSS.read_text(encoding="utf-8")
    root = re.search(r":root\s*\{.*?\n\}", css, flags=re.S)
    assert root is not None, "main.css must define the design tokens in :root"
    return css[: root.start()] + css[root.end() :]


def test_fingerprint_css_stays_inside_the_motion_budget() -> None:
    css = _figure_rules().lower()
    assert "@keyframes" not in css
    assert "animation" not in css
    assert "transition" not in css
    assert "infinite" not in css
    durations = set(re.findall(r"(\d+)ms", css))
    assert durations <= {"0", "80", "140", "220"}


def test_fingerprint_css_uses_tokens_and_zero_radius() -> None:
    css = _figure_rules()
    assert "var(--" in css
    for match in re.finditer(r"border-radius:\s*([^;]+);", css):
        assert match.group(1).strip() in ("0", "0px")
    assert not re.search(r"#[0-9a-fA-F]{3,6}\b", css), (
        "no raw hex outside the :root token block"
    )


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
def test_no_decay_metaphor_anywhere_in_the_science_region(word: str) -> None:
    for path in (FINGERPRINT_JS, FINGERPRINT_CSS, INDEX_HTML):
        assert word not in path.read_text(encoding="utf-8").lower(), (
            f"{path.name} contains decay language: {word!r}"
        )


def test_fingerprint_sources_avoid_novelty_language() -> None:
    for path in (FINGERPRINT_JS, FINGERPRINT_CSS):
        lowered = path.read_text(encoding="utf-8").lower()
        assert "we discovered" not in lowered
        assert "quantum advantage" not in lowered
        assert "breakthrough" not in lowered


# ------------------------------------------------------------ page integration


def test_index_html_mounts_the_figure_and_its_text_equivalent() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert 'id="fingerprint"' in html
    assert 'id="figure-values"' in html
    assert "<figcaption" in html
    # Fragment architecture serves styles from root main.css (no <link> tags);
    # the figure rules must live there.
    css = (REPO_ROOT / "main.css").read_text(encoding="utf-8")
    assert ".figure" in css and ".fingerprint" in css
    # the figure lives in the proof stage, after the two action stages
    assert html.index('id="surprise"') < html.index('id="understanding"')
    assert html.index('id="understanding"') < html.index('id="fingerprint-figure"')


def test_index_html_keeps_exactly_one_announcer() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert html.count('aria-live="polite"') == 1
    assert html.count('role="status"') == 1
    assert 'id="announcer"' in html
    assert "visually-hidden" in html
    assert html.count('role="alert"') == 1


def test_index_html_still_has_no_raw_numbers_for_the_science() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert "0.5078125" not in html, "historical figure in index.html"
    # Beginner magnitudes (|overlap| per d) are kernel-pinned, not invented;
    # full discipline lives in test_copy_contract.py, this pins the figure copy.
    for token in ("0.50", "0.875", "0.969", "0.992"):
        assert token in html


def test_main_js_mounts_the_figure_once() -> None:
    source = MAIN_JS.read_text(encoding="utf-8")
    assert "fingerprint" in source
    assert source.count("mountFingerprint(") == 1
    assert "ui/fingerprint.js" in source


def test_main_js_uses_the_kwargs_call_form_with_backend_first() -> None:
    source = MAIN_JS.read_text(encoding="utf-8")
    code = re.sub(r"/\*.*?\*/", " ", source, flags=re.S)
    code = re.sub(r"//[^\n]*", " ", code)
    assert "callPromisingKwargs" in source
    call = re.search(r"\.callPromisingKwargs\(([^,]+),", code)
    assert call is not None
    # Qollab injects a bare `backend` global; that identifier is forwarded.
    assert call.group(1).strip() == "backend"
    assert ".toJs(" in source


def test_stage_three_ledger_definitions_are_not_duplicated_by_the_figure() -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")
    ledger = re.search(r'<dl id="ledger".*?</dl>', html, flags=re.S)
    assert ledger is not None
    definitions = ledger.group(0)
    # definitions only: no per-dimension values are hard-coded there
    assert ">d=" not in definitions
    assert not re.search(r"\d+\.\d+", definitions)
    values = re.search(r'<dl id="figure-values".*?</dl>', html, flags=re.S)
    assert values is not None
    assert values.group(0) != definitions
