"""Qollab runtime-compliance regressions.

These pin the submission-surface contracts that come from the Qollab runtime
documentation rather than from the product design: a body-fragment entry, a
single root stylesheet, the documented backend-forwarding call shape, lazy
optional Aer imports, static accessibility checks, the required footer credit,
and the IonQ one-job-per-Run failure path.

Nothing here changes the science, the numbers, or the frozen product scope. Every
assertion is static or structural so the whole file runs without a Qollab
browser runtime.
"""

from __future__ import annotations

import html
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

INDEX_HTML = REPO_ROOT / "index.html"
MAIN_JS = REPO_ROOT / "main.js"
MAIN_CSS = REPO_ROOT / "main.css"
LICENSE = REPO_ROOT / "LICENSE"
GALLERY_JS = REPO_ROOT / "ui" / "gallery.js"
EXPERT_JS = REPO_ROOT / "ui" / "expert.js"
FINGERPRINT_JS = REPO_ROOT / "ui" / "fingerprint.js"
HELPS_MODULE = REPO_ROOT / "channels" / "helps_identity_depolarizing.py"

SUPPORT_TEXT = "This effort is supported by Qollab & IonQ"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _strip_html(fragment: str) -> str:
    """Visible text of a fragment, with HTML entities resolved."""
    fragment = re.sub(r"<script\b.*?</script>", " ", fragment, flags=re.S | re.I)
    fragment = re.sub(r"<style\b.*?</style>", " ", fragment, flags=re.S | re.I)
    fragment = re.sub(r"<!--.*?-->", " ", fragment, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", fragment)
    return html.unescape(re.sub(r"\s+", " ", text).strip())


# --------------------------------------------------- 1. body-fragment entry


def test_index_html_is_a_body_fragment_with_no_document_shell() -> None:
    lower = _read(INDEX_HTML).lower()
    assert "<!doctype" not in lower
    for tag in ("html", "head", "body", "script", "link", "style", "base", "meta"):
        # `<header>` and `<button>` are real elements here; only the document
        # shell tags are banned, so match the tag name with a delimiter.
        assert re.search(rf"<{tag}[\s>/]", lower) is None, (
            f"index.html must stay a body fragment: found a <{tag}> shell tag"
        )


def test_index_html_has_no_style_or_asset_attributes() -> None:
    html = _read(INDEX_HTML)
    assert "style=" not in html
    assert "http://" not in html
    assert "https://" not in html
    assert "<img" not in html.lower()


# ----------------------------------------------------- 2. main.css only ship


RETIRED_STYLESHEETS = (
    REPO_ROOT / "styles.css",
    REPO_ROOT / "ui" / "fingerprint.css",
)


@pytest.mark.parametrize("path", RETIRED_STYLESHEETS, ids=lambda p: p.name)
def test_retired_stylesheets_are_deleted(path: Path) -> None:
    assert not path.exists(), (
        f"{path.relative_to(REPO_ROOT)} must be merged into root main.css and deleted; "
        "Qollab loads only main.css for a JS project"
    )


# Companion content that Qollab never loads lives outside the submission
# surface: entangle-lab/ (standalone beginner page), docs/ (mdBook guide),
# brag-output/ (promo video sources). They may carry their own stylesheets;
# the contract below covers only what the Qollab runtime sees.
NON_SUBMISSION_DIRS = frozenset({"entangle-lab", "docs", "brag-output"})


def test_main_css_is_the_only_stylesheet_on_disk() -> None:
    shipped = sorted(
        p.relative_to(REPO_ROOT).as_posix()
        for p in REPO_ROOT.rglob("*.css")
        if ".git" not in p.parts
        and "node_modules" not in p.parts
        and not (NON_SUBMISSION_DIRS & set(p.parts))
    )
    assert shipped == ["main.css"]


def test_no_shipped_source_references_a_retired_stylesheet() -> None:
    for path in (INDEX_HTML, MAIN_JS, MAIN_CSS, GALLERY_JS, EXPERT_JS, FINGERPRINT_JS):
        source = _read(path)
        assert "styles.css" not in source, f"{path.name} still names styles.css"
        assert "fingerprint.css" not in source, f"{path.name} still names fingerprint.css"


def test_main_css_carries_the_merged_figure_gallery_and_expert_rules() -> None:
    css = _read(MAIN_CSS)
    for selector in (
        ":root",
        ".skip",
        "#hero",
        ".ledger",
        "footer",
        ".figure",
        ".fingerprint",
        ".fp-axis",
        ".fp-tick",
        ".fp-mark-a",
        ".fp-mark-b",
        ".fp-lock",
        ".fp-ledger-key",
        ".fp-ledger-value",
        ".gallery-list",
        ".gallery-item",
        ".kind-tag",
        ".expert",
        ".expert-gates",
    ):
        assert selector in css, f"main.css lost the {selector} rule during the merge"


def test_main_css_keeps_every_design_token_value_from_the_merge() -> None:
    """Keep the visual tokens stable as part of the checked-in interface."""
    css = _read(MAIN_CSS)
    expected = {
        "--ink-000": "#0b0e14",
        "--ink-050": "#10141d",
        "--ink-100": "#1b1f2a",
        "--line-grid": "#212936",
        "--line-hairline": "#212936",
        "--line-rule": "#333d4c",
        "--line-control": "#5f6d7d",
        "--text-primary": "#e8edf3",
        "--text-secondary": "#a3adbb",
        "--text-tertiary": "#8b95a3",
        "--accent": "#e9b44c",
        "--accent-ink": "#0b0e14",
        "--accent-quiet": "#3a3222",
        "--data-a": "#a8cde0",
        "--data-b": "#5f8fa8",
        "--sp-1": "4px",
        "--sp-5": "24px",
        "--sp-9": "96px",
        "--label-size": "11px",
        "--body-size": "16px",
        "--readout-size": "18px",
        "--readout-sm": "13px",
        "--meta-mono-size": "12px",
    }
    for token, value in expected.items():
        match = re.search(re.escape(token) + r":\s*([^;]+);", css)
        assert match is not None, f"main.css lost token {token}"
        assert match.group(1).strip() == value, f"{token} changed during the merge"


def test_main_css_raw_hex_lives_only_in_the_token_block() -> None:
    css = _read(MAIN_CSS)
    root = re.search(r":root\s*\{(.*?)\n\}", css, flags=re.S)
    assert root is not None
    outside = css[: root.start()] + css[root.end() :]
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", outside), (
        "component rules must use tokens, never raw hex"
    )


# ------------------------------------------- 3. bare backend + smoke logging


def test_main_js_forwards_the_bare_backend_identifier() -> None:
    source = _read(MAIN_JS)
    code = re.sub(r"/\*.*?\*/", " ", source, flags=re.S)
    code = re.sub(r"//[^\n]*", " ", code)
    call = re.search(r"\.callPromisingKwargs\(([^,]+),", code)
    assert call is not None, "main.js must use callPromisingKwargs(backend, kwargs)"
    assert call.group(1).strip() == "backend", (
        "Qollab injects a bare `backend` global; the forwarded argument must be that "
        f"identifier, got {call.group(1).strip()!r}"
    )


def test_main_js_reads_the_backend_through_a_typeof_guard() -> None:
    """A bare global must never be dereferenced before a typeof check."""
    source = _read(MAIN_JS)
    assert 'typeof backend === "undefined"' in source or (
        "typeof backend" in source and '"undefined"' in source
    )
    guarded = re.search(
        r"function backendProbe\(\)\s*\{.*?\n\}", source, flags=re.S
    )
    assert guarded is not None, "backend access must live in one guarded probe"
    assert "typeof backend" in guarded.group(0)
    assert "typeof globalThis.backend" in guarded.group(0)


def test_main_js_logs_the_backend_smoke_types_on_the_run_path() -> None:
    source = _read(MAIN_JS)
    log = re.search(r"console\.log\((.*?)\n\s*\);", source, flags=re.S)
    assert log is not None, "the smoke path must log to the browser console"
    logged = log.group(1)
    assert "probe.text" in logged, "the logged line must carry the backend probe"
    assert "typeof bridge" in logged, (
        "the smoke line must also record the bridge/ESM call surface"
    )
    probe = re.search(r"function backendProbe\(\)\s*\{(.*?)\n\}", source, flags=re.S)
    assert probe is not None
    body = probe.group(1)
    assert 'typeof backend' in body
    assert 'typeof globalThis.backend' in body
    assert "backend typeof=" in body
    assert "globalThis.backend typeof=" in body


def test_smoke_types_are_recorded_as_run_metadata_text_not_as_a_metric() -> None:
    """The probe belongs in the provenance line, never in a measurement."""
    source = _read(MAIN_JS)
    provenance = re.findall(r"nodes\.provenance\.textContent\s*=[^;]+;", source)
    assert provenance, "main.js must write the provenance line"
    joined = " ".join(provenance)
    assert "backendProbe" in joined, "run metadata text must carry the backend probe"
    for forbidden in ("METRICS[", "empirical_rate", "analytic_value", "ceiling"):
        assert forbidden not in joined, (
            f"the smoke probe must not be folded into a metric: {forbidden}"
        )
    assert re.search(r"nodes\.provenance\.textContent\s*=[^;]*%\s*\.?\+?\s*\(", source) is None


def test_bare_backend_identifier_does_not_shadow_a_local_declaration() -> None:
    """`backend` must stay a free identifier so typeof reflects the runtime."""
    source = _read(MAIN_JS)
    code = re.sub(r"/\*.*?\*/", " ", source, flags=re.S)
    for declaration in (
        r"\bconst\s+backend\b",
        r"\blet\s+backend\b",
        r"\bvar\s+backend\b",
        r"\bfunction\s+backend\b",
        r"\bclass\s+backend\b",
    ):
        assert re.search(declaration, code) is None, (
            f"main.js declares {declaration!r}; the Qollab-injected global must stay free"
        )


# ------------------------------------------------- 4. optional Aer stays lazy


def test_helps_module_has_no_module_scope_aer_import() -> None:
    source = _read(HELPS_MODULE)
    prefix = source.split("def build_b", 1)[0]
    assert "qiskit_aer" not in prefix, "qiskit_aer must be imported inside the builder"


def test_helps_module_imports_aer_only_inside_a_function_body() -> None:
    tree_lines = _read(HELPS_MODULE).splitlines()
    import_lines = [
        (index + 1, line.strip())
        for index, line in enumerate(tree_lines)
        if re.search(r"^\s*(from|import)\s+qiskit_aer", line)
    ]
    assert import_lines, "the builder must still import Aer where it needs it"
    for line_number, line in import_lines:
        assert line_number > next(
            index + 1
            for index, text in enumerate(tree_lines)
            if text.startswith("    def build_b")
        ), f"line {line_number} imports Aer outside the builder: {line}"


def test_registry_import_survives_with_qiskit_aer_blocked() -> None:
    """sys.modules stub, not an import hook: any module-scope Aer import fails."""
    script = r'''
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

# sys.modules stub: any `import qiskit_aer` raises ImportError, so a
# module-scope import anywhere in the registry would fail here.
sys.modules["qiskit_aer"] = None
sys.modules["qiskit_aer.noise"] = None

from channels.api import available_pairs, load_pair, registered_pair_payloads

# Registry discovery and metadata must work with Aer absent.
assert available_pairs() == (
    "comparator-four-pauli",
    "helps-identity-depolarizing",
    "hurts-identity-v",
)
payloads = {item["slug"]: item for item in registered_pair_payloads()}
assert set(payloads) == set(available_pairs())

pair = load_pair("helps-identity-depolarizing")
assert pair.slug == "helps-identity-depolarizing"
assert pair.strategies()[0].bound_kind == "ANALYTIC"

# Channel A is pure Qiskit and still builds.
circuit = pair.build_a(1, 16)
assert circuit.num_qubits == 16

# Channel B is the only Aer-dependent builder and fails loudly, not at import.
try:
    pair.build_b(1, 16)
except ImportError:
    pass
else:
    raise AssertionError("build_b should have raised without qiskit_aer")

# The gallery still discloses the limitation rather than failing the lab.
status = {
    channel["channel"]: channel["status"]
    for channel in payloads["helps-identity-depolarizing"]["circuit"]["channels"]
}
assert status["B"] == "OPTIONAL DEPENDENCY UNAVAILABLE", status
print("ok")
'''
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "ok", completed.stdout


def test_registry_import_survives_when_aer_is_only_a_sys_modules_stub() -> None:
    """The task's stated shape: sys.modules stub, no import hook at all."""
    script = r'''
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
sys.modules["qiskit_aer"] = None
sys.modules["qiskit_aer.noise"] = None

from channels.api import load_pair, registered_pair_payloads

pair = load_pair("helps-identity-depolarizing")
assert pair.build_a(1, 16).num_qubits == 16
try:
    pair.build_b(1, 16)
except ImportError:
    pass
else:
    raise AssertionError("build_b should raise without qiskit_aer")

payloads = {item["slug"]: item for item in registered_pair_payloads()}
status = {
    channel["channel"]: channel["status"]
    for channel in payloads["helps-identity-depolarizing"]["circuit"]["channels"]
}
assert status["B"] == "OPTIONAL DEPENDENCY UNAVAILABLE", status
print("ok")
'''
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "ok", completed.stdout


def test_flagship_registry_import_survives_with_qiskit_aer_blocked() -> None:
    script = r'''
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
sys.modules["qiskit_aer"] = None

from channels.api import load_pair
pair = load_pair("hurts-identity-v")
assert pair.build_a(1, 16).num_qubits == 16
assert pair.build_b(1, 16).num_qubits == 16
print("ok")
'''
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "ok", completed.stdout


# ------------------------------------------------------- 5. accessibility


def _relative_luminance(hex_color: str) -> float:
    value = hex_color.lstrip("#")
    if len(value) == 3:
        value = "".join(char * 2 for char in value)
    channels = [int(value[index : index + 2], 16) / 255 for index in (0, 2, 4)]
    linear = [
        c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast_ratio(foreground: str, background: str) -> float:
    first = _relative_luminance(foreground)
    second = _relative_luminance(background)
    lighter, darker = max(first, second), min(first, second)
    return (lighter + 0.05) / (darker + 0.05)


def _tokens() -> dict:
    return dict(
        re.findall(r"(--[a-z0-9-]+):\s*(#[0-9a-fA-F]{3,8})\s*;", _read(MAIN_CSS))
    )


# Every text/background pair that main.css actually declares. Non-text hairlines
# and decorative borders are deliberately excluded; only meaning-carrying pairs
# are listed here.
TEXT_PAIRS = [
    ("body copy on page", "--text-primary", "--ink-000"),
    ("label on page", "--text-secondary", "--ink-000"),
    ("meta on page", "--text-tertiary", "--ink-000"),
    ("readout on page", "--data-a", "--ink-000"),
    ("display heading on page", "--accent", "--ink-000"),
    ("skip link", "--accent-ink", "--accent"),
    ("button label", "--text-primary", "--ink-100"),
    ("button label on hover", "--text-primary", "--accent-quiet"),
    ("ledger term on page", "--text-secondary", "--ink-000"),
    ("figure value", "--data-a", "--ink-050"),
    ("figure tick label", "--text-tertiary", "--ink-050"),
    ("figure kind tag", "--text-tertiary", "--ink-050"),
    ("figure lock label", "--accent", "--ink-050"),
    ("figure text equivalent", "--text-secondary", "--ink-050"),
    ("gallery value", "--data-a", "--ink-050"),
    ("gallery meta", "--data-a", "--ink-050"),
    ("gallery citation", "--text-secondary", "--ink-050"),
    ("gallery kind tag", "--text-tertiary", "--ink-050"),
    ("expert value", "--data-a", "--ink-050"),
    ("expert meta", "--text-secondary", "--ink-050"),
    ("expert gates", "--data-a", "--ink-000"),
]


@pytest.mark.parametrize(
    "label,foreground,background", TEXT_PAIRS, ids=[pair[0] for pair in TEXT_PAIRS]
)
def test_text_contrast_meets_wcag_aa(label: str, foreground: str, background: str) -> None:
    tokens = _tokens()
    assert foreground in tokens and background in tokens
    ratio = _contrast_ratio(tokens[foreground], tokens[background])
    assert ratio >= 4.5, f"{label}: {foreground} on {background} is {ratio:.2f}:1"


NON_TEXT_PAIRS = [
    ("select control boundary", "--line-control", "--ink-100"),
    ("figure channel B mark", "--data-b", "--ink-050"),
    ("focus ring on page", "--accent", "--ink-000"),
    ("focus ring on figure", "--accent", "--ink-050"),
    ("focus ring on control", "--accent", "--ink-100"),
]


@pytest.mark.parametrize(
    "label,foreground,background",
    NON_TEXT_PAIRS,
    ids=[pair[0] for pair in NON_TEXT_PAIRS],
)
def test_meaningful_non_text_contrast_meets_wcag_aa(
    label: str, foreground: str, background: str
) -> None:
    tokens = _tokens()
    ratio = _contrast_ratio(tokens[foreground], tokens[background])
    assert ratio >= 3.0, f"{label}: {foreground} on {background} is {ratio:.2f}:1"


def test_every_interactive_control_has_a_visible_focus_style() -> None:
    css = _read(MAIN_CSS)
    focus_block = re.search(r"([^{}]*:focus-visible[^{}]*)\{([^}]*)\}", css)
    assert focus_block is not None, "main.css must declare a :focus-visible outline"
    selectors, declarations = focus_block.group(1), focus_block.group(2)
    for control in ("a", "button", "select", "input", "pre"):
        assert f"{control}:focus-visible" in selectors, (
            f"{control} has no visible focus style"
        )
    outline = re.search(r"outline:\s*([^;]+);", declarations)
    assert outline is not None, "the focus rule must set a visible outline"
    assert "2px solid" in outline.group(1)
    assert "outline-offset" in declarations, (
        "the focus ring needs an offset so it never hides the control edge"
    )


def test_prefers_reduced_motion_is_respected() -> None:
    css = _read(MAIN_CSS)
    reduced = re.search(
        r"@media \(prefers-reduced-motion: reduce\)\s*\{(.*?)\n\}", css, flags=re.S
    )
    assert reduced is not None
    block = reduced.group(1)
    assert "transform: none" in block, "the press transform must be dropped"
    assert "scroll-behavior: auto" in block
    # No animation anywhere else could survive the media query.
    assert "@keyframes" not in css
    assert "animation:" not in css
    assert "transition:" not in css


def test_aria_live_region_exists_once_for_results() -> None:
    html = _read(INDEX_HTML)
    assert html.count('aria-live="polite"') == 1
    assert html.count('role="status"') == 1
    assert 'id="announcer"' in html
    assert "visually-hidden" in html
    assert 'role="alert"' in html, "the bridge failure line must be announced"


def test_main_js_writes_results_to_the_aria_live_announcer() -> None:
    source = _read(MAIN_JS)
    assert "roundAnnouncement" in source
    assert "benchmarkAnnouncement" in source
    announcements = re.findall(r"nodes\.announcer\.textContent\s*=", source)
    assert len(announcements) >= 3, (
        "round, benchmark reveal, and probe switch must all announce"
    )


def test_meaning_is_never_carried_by_color_alone() -> None:
    """Kind labels are text, and the two figure marks differ in fill and stroke."""
    html = _strip_html(_read(INDEX_HTML))
    for kind in ("EMPIRICAL", "ANALYTIC", "THEORETICAL CEILING"):
        assert kind in html, f"{kind} must be visible as text"
    css = _read(MAIN_CSS)
    mark_a = re.search(r"\.fp-mark-a\s*\{([^}]*)\}", css)
    mark_b = re.search(r"\.fp-mark-b\s*\{([^}]*)\}", css)
    assert mark_a is not None and mark_b is not None
    # channel B is hollow and 2px, channel A is filled and 1px: shape, not hue.
    assert "fill: var(--ink-050)" in mark_b.group(1)
    assert "stroke-width: 2px" in mark_b.group(1)
    assert "fill: var(--data-a)" in mark_a.group(1)
    gallery = _read(GALLERY_JS)
    assert "KIND_LABELS" in gallery
    for kind in ("EMPIRICAL", "ANALYTIC", "THEORETICAL_CEILING"):
        assert kind in gallery, f"{kind} must be rendered as text in the gallery"


def test_kind_tags_are_rendered_as_text_not_only_as_data_attributes() -> None:
    gallery = _read(GALLERY_JS)
    assert "kind-tag" in gallery
    assert "escapeHtml(row.kindLabel)" in gallery
    expert = _read(EXPERT_JS)
    assert "kindLabel" in expert
    assert "escapeHtml(item.kindLabel)" in expert


def test_fingerprint_figure_keeps_a_text_equivalent() -> None:
    html = _read(INDEX_HTML)
    assert 'id="fingerprint"' in html
    assert 'id="figure-values"' in html
    assert "<figcaption" in html
    fingerprint = _read(FINGERPRINT_JS)
    assert "export function textEquivalent" in fingerprint
    assert 'role="img"' in fingerprint
    assert "aria-label" in fingerprint
    markup = _run_node("console.log(fp.textEquivalent(fp.figureModel()).length);")
    assert markup == "4", "one text-equivalent row per plotted dimension"


def test_figure_and_expert_material_is_scrollable_without_hiding_the_text() -> None:
    css = _read(MAIN_CSS)
    for rule, selector in (
        (r"\.figure\s*\{([^}]*)\}", ".figure"),
        (r"\.expert-gates\s*\{([^}]*)\}", ".expert-gates"),
    ):
        block = re.search(rule, css)
        assert block is not None, f"{selector} rule is missing from main.css"
        assert "overflow-x: auto" in block.group(1), (
            f"{selector} must stay horizontally scrollable for small viewports"
        )
    assert 'tabindex="0"' in _read(INDEX_HTML), (
        "the scrollable benchmark readout must be keyboard reachable"
    )
    assert 'tabindex=\\"0\\"' in _read(EXPERT_JS), (
        "scrollable circuit disclosure must be keyboard reachable"
    )


def test_keyboard_operability_of_the_whole_flow() -> None:
    html = _read(INDEX_HTML)
    # Native controls only, no positive tabindex, no inline handlers, no div buttons.
    for tag in ("button", "select", "input"):
        assert f"<{tag}" in html
    assert 'type="radio"' in html
    assert "<fieldset" in html and "<legend" in html
    for match in re.finditer(r'tabindex="([^"]*)"', html):
        value = match.group(1).strip().lstrip("+")
        assert not value.isdigit() or int(value) == 0
    for banned in ("onclick=", "onkeydown=", 'role="button"'):
        assert banned not in html
    # Escape closes the expert drawer and returns focus to its toggle.
    expert = _read(EXPERT_JS)
    assert 'event.key === "Escape"' in expert
    assert "nodes.toggle.focus()" in expert
    assert 'aria-expanded' in expert
    assert 'aria-controls="expert-drawer"' in html


def test_skip_link_targets_a_real_landmark() -> None:
    html = _read(INDEX_HTML)
    assert re.search(r'<a class="skip" href="#([\w-]+)"', html)
    target = re.search(r'<a class="skip" href="#([\w-]+)"', html).group(1)
    assert f'id="{target}"' in html
    assert ".skip:focus" in _read(MAIN_CSS)


# ------------------------------------------ 6. required text, license, no auth


def test_footer_contains_the_exact_required_support_credit() -> None:
    html = _read(INDEX_HTML)
    footer = re.search(r"<footer.*?</footer>", html, flags=re.S)
    assert footer is not None, "index.html must have a footer"
    visible = _strip_html(footer.group(0))
    assert SUPPORT_TEXT in visible, (
        f"footer must contain exactly {SUPPORT_TEXT!r}; got {visible!r}"
    )


def test_required_support_credit_is_not_duplicated_or_altered() -> None:
    visible = _strip_html(_read(INDEX_HTML))
    assert visible.count(SUPPORT_TEXT) == 1
    for variant in ("supported by Qollab & IonQ.", "Supported by Qollab and IonQ"):
        if variant == SUPPORT_TEXT:
            continue
        assert variant not in visible, f"credit variant leaked: {variant!r}"


def test_license_is_mit() -> None:
    text = _read(LICENSE)
    assert text.lstrip().startswith("MIT License"), "LICENSE must be the MIT license"
    assert "MIT License" in text
    assert "Permission is hereby granted, free of charge" in text
    for banned in ("Apache License", "GNU GENERAL PUBLIC LICENSE", "BSD", "GPL"):
        assert banned not in text, f"LICENSE is not MIT: found {banned!r}"


def test_no_sign_in_or_authentication_anywhere_in_shipped_sources() -> None:
    for path in (
        INDEX_HTML,
        MAIN_JS,
        MAIN_CSS,
        GALLERY_JS,
        EXPERT_JS,
        FINGERPRINT_JS,
    ):
        lowered = _read(path).lower()
        for banned in (
            "sign in",
            "signin",
            "sign-in",
            "log in",
            "login",
            "log-in",
            "sign up",
            "signup",
            "api key",
            "api_key",
            "apikey",
            "access token",
            "bearer ",
            "password",
        ):
            assert banned not in lowered, f"{path.name} contains {banned!r}"


# ---------------------------------------- 7. IonQ one-job-per-Run error path


ONE_JOB_MESSAGE_MARKERS = (
    "ONE BACKEND JOB",
    "NEW QOLLAB RUN",
)


def test_one_job_failure_path_names_the_run_constraint_without_numbers() -> None:
    source = _read(MAIN_JS)
    handler = re.search(
        r"function reportBridgeFailure\(error\)\s*\{(.*?)\n\}", source, flags=re.S
    )
    assert handler is not None, "the bridge failure handler must exist"
    body = handler.group(1)
    literals = " ".join(re.findall(r'"([^"]*)"', body))
    for marker in ONE_JOB_MESSAGE_MARKERS:
        assert marker in literals, f"failure copy must state {marker!r}: {literals!r}"
    # A failure message must never present an invented measurement.
    assert "%" not in literals
    assert not re.search(r"\d+\.\d+", literals), (
        f"the failure copy must not carry a result number: {literals!r}"
    )
    assert "NO VERIFIED RESULT" in source


def test_one_job_failure_path_never_reenables_a_second_job() -> None:
    """A consumed IonQ job cannot be retried inside the same Run."""
    source = _read(MAIN_JS)
    handler = re.search(
        r"function reportBridgeFailure\(error\)\s*\{(.*?)\n\}", source, flags=re.S
    )
    assert handler is not None
    body = handler.group(1)
    assert "nodes.run.disabled = true" in body, (
        "after a backend job is spent the Run must not offer another one"
    )
    assert "nodes.run.disabled = false" not in body
    assert "nodes.run.textContent" in body, "the control must say why it is closed"


def test_local_simulation_is_not_constrained_by_the_one_job_rule() -> None:
    """The rule is a Qollab/IonQ Run property, not a bridge-wide limit."""
    bridge_source = _read(REPO_ROOT / "quantum" / "bridge.py")
    code = re.sub(r'"""(?:.|\n)*?"""', " ", bridge_source)
    assert "backend.run" not in code, "the bridge delegates, it does not call run"
    assert "run_batch(" in bridge_source
    main = _read(MAIN_JS)
    assert main.count('callBridge("get_experience"') == 1
    assert main.count('callBridge("get_gallery"') == 1
    for retired in (
        'callBridge("get_round"',
        'callBridge("get_benchmark"',
        'callBridge("get_batch"',
    ):
        assert retired not in main, f"retired multi-job entry still called: {retired}"


def test_cached_reveal_never_resubmits_a_job() -> None:
    source = _read(MAIN_JS)
    handler = re.search(
        r"document\.getElementById\("
        r'"round-form"\)\.addEventListener\("submit",\s*'
        r"function \(event\)\s*\{(.*?)\n\}\);",
        source,
        flags=re.S,
    )
    assert handler is not None
    body = handler.group(1)
    assert "if (experience)" in body
    assert "EVIDENCE CACHED" in body
    assert body.index("if (experience)") < body.index('callBridge("get_experience"')


def _run_node(expression: str) -> str:
    script = (
        "const fp = await import('%s');\n" % FINGERPRINT_JS.as_uri()
        + expression
        + "\n"
    )
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return completed.stdout.strip()


def test_touched_javascript_parses_as_an_es_module() -> None:
    for path in (MAIN_JS, GALLERY_JS, EXPERT_JS, FINGERPRINT_JS):
        completed = subprocess.run(
            ["node", "--check", str(path)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            check=False,
        )
        assert completed.returncode == 0, f"{path.name}: {completed.stderr}"


def test_no_secret_like_strings_in_the_repository() -> None:
    """Belt-and-braces against credentials leaking into a public submission."""
    pattern = re.compile(
        r"(sk-[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{12,}"
        r"|-----BEGIN [A-Z ]*PRIVATE KEY-----)"
    )
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        parts = path.parts
        if ".git" in parts or "node_modules" in parts or "__pycache__" in parts:
            continue
        if path.suffix.lower() in (".png", ".jpg", ".pyc"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        assert pattern.search(text) is None, f"possible secret in {path}"


def test_claims_file_is_untouched_by_the_runtime_surface() -> None:
    """Runtime compliance must never rewrite the claim registry."""
    claims = json.loads(_read(REPO_ROOT / "claims.json"))
    assert isinstance(claims, (list, dict))
    text = _read(REPO_ROOT / "claims.json")
    assert "0.5078125" in text or "0.507781982421875" in text
