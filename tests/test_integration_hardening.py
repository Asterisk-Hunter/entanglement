"""Regression tests for issues found while integrating the agent branches."""

from __future__ import annotations

from pathlib import Path

import pytest

from quantum.engine import benchmark_strategy
from quantum.results import BatchResult, CircuitSpec, Provenance
from quantum.science import helstrom_ceiling, simple_success

REPO_ROOT = Path(__file__).resolve().parents[1]


def _dimension_four_batch(shots: int = 100) -> BatchResult:
    equal = (("0", "0"), ("0", "0"))
    unequal = (("0", "0"), ("1", "0"))
    circuits = (
        CircuitSpec("sep_I", "SEPARABLE", "A"),
        CircuitSpec("sep_V", "SEPARABLE", "B"),
        CircuitSpec("me_I", "MAX_ENTANGLEMENT", "A"),
        CircuitSpec("me_V", "MAX_ENTANGLEMENT", "B"),
    )
    outcomes = {
        "sep_I": {equal: shots},
        "sep_V": {unequal: shots},
        "me_I": {equal: shots},
        "me_V": {equal: shots // 4, unequal: shots - shots // 4},
    }
    return BatchResult(
        pair_slug="hurts-identity-v",
        dimension=4,
        total_qubits=16,
        num_system_qubits=2,
        shots=shots,
        circuits=circuits,
        counts={spec.name: {} for spec in circuits},
        outcomes=outcomes,
        provenance=Provenance.LIVE_LOCAL,
        backend_name="integration-fixture",
        result_mapping="by-name",
    )


def test_benchmark_analytic_values_follow_the_batch_dimension() -> None:
    benchmark = benchmark_strategy(_dimension_four_batch(), "hurts-max-entanglement")
    assert benchmark.dimension == 4
    assert benchmark.empirical_rate == pytest.approx(simple_success(4), abs=1e-12)
    assert benchmark.analytic_value == pytest.approx(simple_success(4), abs=1e-15)
    assert benchmark.ceiling == pytest.approx(helstrom_ceiling(4), abs=1e-15)


def test_qollab_bridge_conversion_is_plain_js_and_releases_the_proxy() -> None:
    source = (REPO_ROOT / "main.js").read_text(encoding="utf-8")
    assert "dict_converter: Object.fromEntries" in source
    assert "create_pyproxies: false" in source
    assert "proxy.destroy()" in source


def test_gitignore_has_real_line_breaks_for_generated_artifacts() -> None:
    lines = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "__pycache__/" in lines
    assert "*.pyc" in lines
    assert ".pytest_cache/" in lines
    assert "node_modules/" in lines
