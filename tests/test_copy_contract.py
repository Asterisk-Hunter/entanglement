"""Integrated copy, accessibility, styling, and JS bridge contracts."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = REPO_ROOT / "index.html"
MAIN_JS = REPO_ROOT / "main.js"
MAIN_CSS = REPO_ROOT / "main.css"
GAME_JS = REPO_ROOT / "ui" / "game.js"
BENCHMARK_JS = REPO_ROOT / "ui" / "benchmark.js"
GALLERY_JS = REPO_ROOT / "ui" / "gallery.js"
EXPERT_JS = REPO_ROOT / "ui" / "expert.js"

HERO_LINES = ["TWO BLACK BOXES.", "ONE USE.", "PICK YOUR PROBE."]
QUARANTINED_FIGURE = "0.5078125"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _strip_html(html: str) -> str:
    html = re.sub(r"<script\b.*?</script>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<style\b.*?</style>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<!--.*?-->", " ", html, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


def _ui_sources() -> str:
    return "\n".join(
        _read(path)
        for path in (
            INDEX_HTML,
            MAIN_JS,
            MAIN_CSS,
            GAME_JS,
            BENCHMARK_JS,
            GALLERY_JS,
            EXPERT_JS,
        )
    )


def test_hero_copy_is_exact_three_short_lines() -> None:
    html = _read(INDEX_HTML)
    for line in HERO_LINES:
        assert f">{line}<" in html
        assert len(line.split()) <= 4


def test_probe_and_runtime_controls_are_explicit() -> None:
    html = _read(INDEX_HTML)
    assert 'value="SEPARABLE"' in html
    assert 'value="MAX_ENTANGLEMENT"' in html
    assert re.findall(r'<option value="(100|500|2000)"', html) == ["100", "500", "2000"]
    assert 'option value="256"' in html
    assert 'option value="64"' in html


def test_primary_actions_match_final_flow() -> None:
    html = _strip_html(_read(INDEX_HTML))
    assert "PLAY ONE ROUND" in html
    assert "REVEAL STRATEGY TEST" in html
    assert "COMPARE SEPARABLE" in html
    assert "SHOW EXPERT EVIDENCE" in html
    assert "RESOURCE LAB" in html


def test_value_kinds_are_visible_as_text() -> None:
    visible = _strip_html(_read(INDEX_HTML)) + _read(GALLERY_JS) + _read(EXPERT_JS)
    for label in ("EMPIRICAL", "ANALYTIC", "THEORETICAL CEILING"):
        assert label in visible


def test_quarantined_figure_never_surfaces_in_browser_sources() -> None:
    sources = _ui_sources()
    assert QUARANTINED_FIGURE not in sources
    assert "5078125" not in sources


def test_no_unqualified_advantage_or_discovery_claim() -> None:
    visible = _strip_html(_read(INDEX_HTML)).lower()
    assert "no computational advantage is claimed" in visible
    for phrase in ("we discovered", "new theorem", "breakthrough"):
        assert phrase not in visible


def test_main_uses_one_live_experience_call_and_zero_job_gallery_call() -> None:
    source = _read(MAIN_JS)
    assert source.count('callBridge("get_experience"') == 1
    assert source.count('callBridge("get_gallery"') == 1
    assert 'callBridge("get_round"' not in source
    assert 'callBridge("get_benchmark"' not in source
    assert "get_batch" not in source


def test_qollab_bridge_conversion_is_plain_js_and_releases_proxy() -> None:
    source = _read(MAIN_JS)
    assert ".callPromisingKwargs(" in source
    assert "globalThis.backend" in source
    assert ".toJs({" in source
    assert "dict_converter: Object.fromEntries" in source
    assert "create_pyproxies: false" in source
    assert "proxy.destroy()" in source


def test_browser_code_does_not_import_aer_or_execute_python_strings() -> None:
    for path in (INDEX_HTML, MAIN_JS, GAME_JS, BENCHMARK_JS, GALLERY_JS, EXPERT_JS):
        source = _read(path)
        assert "qiskit_aer" not in source
        assert "AerSimulator" not in source
        assert "runPython" not in source
    assert "eval(" not in _read(MAIN_JS)


def test_gallery_and_expert_have_no_pair_specific_branching() -> None:
    gallery = _read(GALLERY_JS)
    expert = _read(EXPERT_JS)
    for slug in ("hurts-identity-v", "helps-identity-depolarizing"):
        assert slug not in gallery
        assert slug not in expert
    assert "PAIR_ENTRIES" not in gallery
    assert "flagshipEntry" not in expert
    assert "EXECUTABLE " not in expert
    assert "ROUND SELECTION SEED" in expert


def test_document_order_and_landmarks_are_accessible() -> None:
    html = _read(INDEX_HTML)
    assert html.count("<header") == 1
    assert html.count("<main") == 1
    assert html.count("<section") == 4
    order = [
        html.index(f'id="{stage}"')
        for stage in ("surprise", "understanding", "proof", "resource-lab")
    ]
    assert order == sorted(order)
    assert 'class="skip"' in html and 'href="#proof"' in html
    assert html.count('type="radio"') == 2
    assert html.count('aria-live="polite"') == 1
    assert html.count('role="alert"') == 1
    assert 'aria-expanded="false"' in html
    assert 'aria-controls="expert-drawer"' in html


def test_no_positive_tabindex_or_inline_handlers() -> None:
    html = _read(INDEX_HTML)
    for match in re.finditer(r'tabindex="([^"]*)"', html):
        value = match.group(1).strip().lstrip("+")
        assert not value.isdigit() or int(value) == 0
    assert "onclick=" not in html
    assert 'role="button"' not in html


REQUIRED_TOKENS = [
    "--ink-000",
    "--ink-050",
    "--ink-100",
    "--line-grid",
    "--line-rule",
    "--line-control",
    "--text-primary",
    "--text-secondary",
    "--text-tertiary",
    "--accent",
    "--accent-ink",
    "--data-a",
    "--data-b",
]


@pytest.mark.parametrize("token", REQUIRED_TOKENS)
def test_design_token_is_defined_in_qollab_stylesheet(token: str) -> None:
    assert f"{token}:" in _read(MAIN_CSS)


def test_qollab_stylesheet_has_zero_radius_and_no_visual_gimmicks() -> None:
    css = _read(MAIN_CSS).lower()
    for match in re.finditer(r"border-radius:\s*([^;]+);", css):
        assert match.group(1).strip() in ("0", "0px")
    for banned in ("backdrop-filter", "linear-gradient", "radial-gradient", "@keyframes", "infinite"):
        assert banned not in css


def test_focus_and_reduced_motion_contracts_exist() -> None:
    css = _read(MAIN_CSS)
    assert "outline: 2px solid var(--accent)" in css
    assert "@media (prefers-reduced-motion: reduce)" in css
    assert "transform: none" in css


def test_index_has_no_embedded_style_or_external_asset_dependency() -> None:
    html = _read(INDEX_HTML)
    assert "<style" not in html
    assert "style=" not in html
    assert "<link" not in html
    assert "http://" not in html
    assert "https://" not in html
