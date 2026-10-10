"""Regression contracts for the integrated tree.

These tests pin the integration findings that must stay fixed as the tree evolves.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from channels.api import load_pair, registered_pair_payloads
from quantum import bridge
from quantum.science import helstrom_ceiling, simple_success

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_flagship_analytics_follow_the_runtime_dimension() -> None:
    pair = load_pair("hurts-identity-v")
    bounds = pair.analytic_bounds_for(4)
    assert bounds["max_entanglement_simple"] == pytest.approx(simple_success(4), abs=1e-15)
    assert bounds["helstrom_ceiling"] == pytest.approx(helstrom_ceiling(4), abs=1e-15)


def test_gallery_payload_is_registry_driven_and_bridge_exposed() -> None:
    payloads = registered_pair_payloads()
    assert {item["slug"] for item in payloads} == {
        "hurts-identity-v",
        "helps-identity-depolarizing",
        "comparator-four-pauli",
    }
    result = bridge.get_gallery(None)
    assert result["kind"] == "GalleryResult"
    assert result["total_backend_jobs"] == 0
    assert {item["slug"] for item in result["pairs"]} == {item["slug"] for item in payloads}


def test_helps_entangled_number_is_a_ceiling_not_an_executable_strategy() -> None:
    pair = load_pair("helps-identity-depolarizing")
    strategies = {strategy.probe_kind: strategy for strategy in pair.strategies()}
    max_ent = strategies["MAX_ENTANGLEMENT"]
    assert max_ent.bound_kind == "THEORETICAL_CEILING"
    assert max_ent.analytic_value == pytest.approx(0.875, abs=1e-15)


def test_frontend_keeps_one_job_hero_and_runtime_generic_gallery() -> None:
    main_source = (REPO_ROOT / "main.js").read_text(encoding="utf-8")
    gallery_source = (REPO_ROOT / "ui" / "gallery.js").read_text(encoding="utf-8")
    expert_source = (REPO_ROOT / "ui" / "expert.js").read_text(encoding="utf-8")

    assert 'callBridge("get_experience"' in main_source
    assert 'callBridge("get_round"' not in main_source
    assert 'callBridge("get_benchmark"' not in main_source
    assert 'callBridge("get_gallery"' in main_source
    assert "dict_converter: Object.fromEntries" in main_source
    assert "proxy.destroy()" in main_source

    assert "PAIR_ENTRIES" not in gallery_source
    assert "hurts-identity-v" not in gallery_source
    assert "helps-identity-depolarizing" not in gallery_source
    assert "flagshipEntry" not in expert_source
    assert "EXECUTABLE " not in expert_source
    assert "ROUND SELECTION SEED" in expert_source


def test_helps_optional_aer_is_not_imported_at_module_scope() -> None:
    source = (REPO_ROOT / "channels" / "helps_identity_depolarizing.py").read_text(
        encoding="utf-8"
    )
    prefix = source.split("def build_b", 1)[0]
    assert "qiskit_aer" not in prefix
