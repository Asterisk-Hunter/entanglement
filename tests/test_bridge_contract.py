"""Contract tests for the Qollab browser bridge.

The bridge is the only thing that crosses the JS/Python boundary, so everything
here is about the shape of what crosses: explicit `kind` and `provenance`
fields, JSON-only values, and a round schema that cannot be mistaken for a
benchmark schema.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from quantum.bridge import (  # noqa: E402
    BRIDGE_FUNCTIONS,
    MAX_LIVE_DIMENSION,
    bridge_info,
    get_batch,
    get_benchmark,
    get_round,
)
from quantum.results import PROVENANCE_VALUES  # noqa: E402
from quantum.science import (  # noqa: E402
    SEPARABLE_SUCCESS,
    helstrom_ceiling,
    simple_success,
)

FLAGSHIP_D = 256
FLAGGESHIP_N = 8
TOTAL_QUBITS = 16


# --------------------------------------------------------------- fake backend


class _FakeJob:
    def __init__(self, result) -> None:
        self._result = result

    def result(self):
        return self._result


class _FakeBackend:
    """Deterministic stand-in: no Qiskit execution, no Aer, no qiskit_aer."""

    name = "fake-gate0-backend"

    def __init__(self, counts_by_name: dict) -> None:
        self.counts_by_name = counts_by_name
        self.run_calls: list = []

    def run(self, circuits, **kwargs):
        self.run_calls.append((list(circuits), dict(kwargs)))
        entries = [(c.name, self.counts_by_name[c.name]) for c in circuits]
        return _FakeJob(_Entries(entries))


class _Counts:
    def __init__(self, counts: dict) -> None:
        self.counts = counts


class _Header:
    def __init__(self, name: str | None) -> None:
        self.name = name


class _Experiment:
    def __init__(self, name, counts) -> None:
        self.header = _Header(name)
        self.data = _Counts(counts)


class _Entries:
    def __init__(self, entries: list) -> None:
        self.results = [_Experiment(name, counts) for name, counts in entries]

    def get_counts(self, name: str) -> dict:
        for experiment in self.results:
            if experiment.header.name == name:
                return experiment.data.counts
        raise KeyError(name)


def _key(total_qubits: int, set_qubits) -> str:
    chars = ["0"] * total_qubits
    for qubit in set_qubits:
        chars[total_qubits - 1 - qubit] = "1"
    return "".join(chars)


def _sep_counts(total_qubits: int, channel_b: bool, shots: int) -> dict:
    return {_key(total_qubits, {0} if channel_b else set()): shots}


def _me_counts(total_qubits: int, channel_b: bool, shots: int, overlap: float) -> dict:
    if channel_b:
        agreeing = round(shots * overlap**2)
        disagreeing = shots - agreeing
        match = _key(total_qubits, set())
        mismatch = _key(total_qubits, {2 * FLAGGESHIP_N - 1})
        counts = {}
        if agreeing:
            counts[match] = agreeing
        if disagreeing:
            counts[mismatch] = disagreeing
        return counts
    return {_key(total_qubits, set()): shots}


def gate0_counts(shots: int = 1000, overlap: float = -0.9921875) -> dict:
    return {
        "sep_I": _sep_counts(TOTAL_QUBITS, False, shots),
        "sep_V": _sep_counts(TOTAL_QUBITS, True, shots),
        "me_I": _me_counts(TOTAL_QUBITS, False, shots, overlap),
        "me_V": _me_counts(TOTAL_QUBITS, True, shots, overlap),
    }


# ------------------------------------------------------------- bridge surface


def test_bridge_info_declares_its_callable_surface() -> None:
    info = bridge_info()
    assert set(info["functions"]) == set(BRIDGE_FUNCTIONS)
    for name in BRIDGE_FUNCTIONS:
        assert name in info["functions"]
        assert callable(info["functions"][name])
        assert isinstance(info["functions"][name].__doc__, str)


def test_bridge_info_is_json_serializable() -> None:
    payload = {k: v for k, v in bridge_info().items() if k != "functions"}
    assert json.loads(json.dumps(payload)) == payload


def test_every_bridge_function_response_is_a_plain_json_value() -> None:
    backend = _FakeBackend(gate0_counts())
    responses = [
        get_batch(backend, shots=1000),
        get_round(backend, probe_kind="MAX_ENTANGLEMENT", shots=1, rng_seed=4),
        get_round(backend, probe_kind="SEPARABLE", shots=1, rng_seed=4),
        get_benchmark(backend, shots=1000, strategy_slug="hurts-max-entanglement"),
        get_benchmark(backend, shots=1000, strategy_slug="hurts-separable"),
    ]
    for response in responses:
        assert type(response) is dict
        assert json.loads(json.dumps(response)) == response


def test_no_python_proxy_types_cross_the_boundary() -> None:
    """Every value must be a plain JSON scalar/container, never a proxy."""
    backend = _FakeBackend(gate0_counts(shots=200))
    responses = [
        get_batch(backend, shots=200),
        get_round(backend, probe_kind="SEPARABLE", shots=1, rng_seed=2),
        get_benchmark(backend, shots=200, strategy_slug="hurts-max-entanglement"),
    ]

    def walk(value, path="$"):
        if isinstance(value, dict):
            assert type(value) is dict, f"{path} is {type(value)}"
            for key, item in value.items():
                assert type(key) is str, f"{path} key {type(key)}"
                walk(item, f"{path}.{key}")
        elif isinstance(value, list):
            assert type(value) is list, f"{path} is {type(value)}"
            for index, item in enumerate(value):
                walk(item, f"{path}[{index}]")
        else:
            assert value is None or type(value) in (
                str,
                int,
                float,
                bool,
            ), f"{path} is {type(value)}"

    for response in responses:
        walk(response)


def test_batch_response_declares_kind_and_provenance() -> None:
    response = get_batch(_FakeBackend(gate0_counts()), shots=1000)
    assert response["kind"] == "BatchResult"
    assert response["provenance"] in PROVENANCE_VALUES
    assert response["is_live"] is True
    assert response["backend"] == "fake-gate0-backend"
    assert response["dimension"] == FLAGSHIP_D
    assert response["total_qubits"] == TOTAL_QUBITS
    assert response["shots"] == 1000
    assert response["result_mapping"] in ("by-name", "by-position")
    assert response["pair_slug"] == "hurts-identity-v"
    assert [entry["name"] for entry in response["circuits"]] == [
        "sep_I",
        "sep_V",
        "me_I",
        "me_V",
    ]


def test_batch_response_exposes_the_four_circuit_counts() -> None:
    response = get_batch(_FakeBackend(gate0_counts()), shots=1000)
    assert set(response["counts"]) == {"sep_I", "sep_V", "me_I", "me_V"}
    for counts in response["counts"].values():
        assert isinstance(counts, dict)
        for key, value in counts.items():
            assert isinstance(key, str) and len(key) == TOTAL_QUBITS
            assert isinstance(value, int) and value >= 0


def test_batch_response_reports_one_backend_run() -> None:
    backend = _FakeBackend(gate0_counts())
    get_batch(backend, shots=1000)
    assert len(backend.run_calls) == 1
    circuits, kwargs = backend.run_calls[0]
    assert [c.name for c in circuits] == ["sep_I", "sep_V", "me_I", "me_V"]
    assert kwargs["shots"] == 1000


def test_batch_response_marks_precomputed_provenance_never_live() -> None:
    from quantum.results import BatchResult

    precomputed = BatchResult.from_precomputed(
        counts=gate0_counts(shots=100),
        shots=100,
        dimension=FLAGSHIP_D,
        total_qubits=TOTAL_QUBITS,
        pair_slug="hurts-identity-v",
    )
    payload = precomputed.to_payload()
    assert payload["provenance"] == "precomputed"
    assert payload["is_live"] is False
    assert payload["backend"] == "precomputed-fixture"


# ------------------------------------------------------------ round contract


def test_round_response_declares_kind_and_carries_no_rate() -> None:
    response = get_round(
        _FakeBackend(gate0_counts()), probe_kind="MAX_ENTANGLEMENT", shots=1, rng_seed=1
    )
    assert response["kind"] == "RoundResult"
    assert response["provenance"] in PROVENANCE_VALUES
    assert response["hidden_channel"] in ("A", "B")
    assert response["guess"] in ("A", "B")
    assert isinstance(response["won"], bool)
    assert response["won"] == (response["guess"] == response["hidden_channel"])


@pytest.mark.parametrize(
    "forbidden",
    ["rate", "win_rate", "probability", "success", "trials", "shots",
     "ci_low", "ci_high", "analytic_value", "ceiling", "empirical_rate"],
)
def test_round_response_has_no_benchmark_or_rate_fields(forbidden: str) -> None:
    response = get_round(
        _FakeBackend(gate0_counts()), probe_kind="SEPARABLE", shots=1, rng_seed=1
    )
    assert forbidden not in response


def test_round_and_benchmark_schemas_cannot_be_confused() -> None:
    backend = _FakeBackend(gate0_counts(shots=1000))
    round_response = get_round(backend, probe_kind="SEPARABLE", shots=1, rng_seed=5)
    benchmark = get_benchmark(backend, shots=1000, strategy_slug="hurts-separable")
    batch = get_batch(backend, shots=1000)

    assert round_response["kind"] == "RoundResult"
    assert benchmark["kind"] == "StrategyBenchmark"
    assert batch["kind"] == "BatchResult"
    assert len({round_response["kind"], benchmark["kind"], batch["kind"]}) == 3

    # Neither response may carry the other's distinguishing fields.
    for field in ("hidden_channel", "guess", "won"):
        assert field not in benchmark
    for field in ("trials", "empirical_rate", "analytic_value", "ceiling", "ci_low"):
        assert field not in round_response


def test_round_outcome_is_two_bit_strings() -> None:
    response = get_round(
        _FakeBackend(gate0_counts()), probe_kind="MAX_ENTANGLEMENT", shots=1, rng_seed=9
    )
    halves = response["outcome"]
    assert isinstance(halves, list) and len(halves) == 2
    for half in halves:
        assert isinstance(half, str)
        assert len(half) == FLAGGESHIP_N
        set(half) <= {"0", "1"}


def test_round_response_rejects_unknown_probe_kind() -> None:
    with pytest.raises(ValueError):
        get_round(
            _FakeBackend(gate0_counts()), probe_kind="PARTIAL", shots=1, rng_seed=1
        )


def test_round_response_is_reproducible_for_a_fixed_seed() -> None:
    first = get_round(
        _FakeBackend(gate0_counts()), probe_kind="SEPARABLE", shots=1, rng_seed=3
    )
    second = get_round(
        _FakeBackend(gate0_counts()), probe_kind="SEPARABLE", shots=1, rng_seed=3
    )
    assert first == second


# -------------------------------------------------------- benchmark contract


def test_benchmark_response_declares_kind_and_separates_the_numbers() -> None:
    response = get_benchmark(
        _FakeBackend(gate0_counts(shots=1000)),
        shots=1000,
        strategy_slug="hurts-max-entanglement",
    )
    assert response["kind"] == "StrategyBenchmark"
    assert response["provenance"] in PROVENANCE_VALUES
    assert response["trials"] == 2000
    assert response["shots_per_channel"] == 1000
    assert response["empirical_kind"] == "EMPIRICAL"
    assert response["analytic_kind"] == "ANALYTIC"
    assert response["ceiling_kind"] == "THEORETICAL_CEILING"
    assert 0.0 <= response["ci_low"] <= response["ci_high"] <= 1.0
    assert isinstance(response["analytic_value"], float)
    assert isinstance(response["ceiling"], float)
    assert response["analytic_value"] != response["ceiling"]


def test_benchmark_analytic_value_matches_the_kernel() -> None:
    response = get_benchmark(
        _FakeBackend(gate0_counts(shots=1000)),
        shots=1000,
        strategy_slug="hurts-max-entanglement",
    )
    assert response["analytic_value"] == pytest.approx(simple_success(FLAGSHIP_D), abs=1e-15)
    assert response["ceiling"] == pytest.approx(helstrom_ceiling(FLAGSHIP_D), abs=1e-15)
    assert response["empirical_rate"] == pytest.approx(
        simple_success(FLAGSHIP_D), abs=5e-4
    )


def test_benchmark_separable_is_perfect() -> None:
    response = get_benchmark(
        _FakeBackend(gate0_counts(shots=1000)),
        shots=1000,
        strategy_slug="hurts-separable",
    )
    assert response["analytic_value"] == pytest.approx(SEPARABLE_SUCCESS, abs=1e-15)
    assert response["ceiling"] == pytest.approx(SEPARABLE_SUCCESS, abs=1e-15)
    assert response["empirical_rate"] == pytest.approx(1.0, abs=1e-12)


def test_benchmark_response_rejects_unknown_strategy() -> None:
    with pytest.raises(KeyError):
        get_benchmark(
            _FakeBackend(gate0_counts(shots=100)),
            shots=100,
            strategy_slug="hurts-nope",
        )


def test_benchmark_response_carries_a_human_label() -> None:
    response = get_benchmark(
        _FakeBackend(gate0_counts(shots=100)),
        shots=100,
        strategy_slug="hurts-separable",
    )
    assert isinstance(response["strategy_label"], str)
    assert response["strategy_label"]


# ---------------------------------------------------------- dimension guard


def test_no_bridge_entry_point_allows_a_live_dimension_above_the_cap() -> None:
    assert MAX_LIVE_DIMENSION == 256
    backend = _FakeBackend(gate0_counts(shots=10))
    for call in (
        lambda: get_batch(backend, shots=10, d=1024, total_qubits=32),
        lambda: get_round(backend, probe_kind="SEPARABLE", shots=1, d=1024, total_qubits=32),
        lambda: get_benchmark(
            backend, shots=10, strategy_slug="hurts-separable", d=1024, total_qubits=32
        ),
    ):
        with pytest.raises(ValueError):
            call()


def test_bridge_rejects_non_power_of_two_dimension() -> None:
    backend = _FakeBackend(gate0_counts(shots=10))
    with pytest.raises(ValueError):
        get_batch(backend, shots=10, d=3)


def test_bridge_rejects_bad_shots() -> None:
    backend = _FakeBackend(gate0_counts(shots=10))
    with pytest.raises(ValueError):
        get_batch(backend, shots=0)
    with pytest.raises(ValueError):
        get_batch(backend, shots=-5)


# ------------------------------------------------------------- provenance


def test_batch_provenance_can_be_marked_remote() -> None:
    response = get_batch(
        _FakeBackend(gate0_counts(shots=100)),
        shots=100,
        provenance="live-remote",
    )
    assert response["provenance"] == "live-remote"
    assert response["is_live"] is True


def test_batch_provenance_rejects_unknown_label() -> None:
    with pytest.raises(ValueError):
        get_batch(
            _FakeBackend(gate0_counts(shots=100)), shots=100, provenance="cached"
        )


def test_batch_provenance_refuses_precomputed() -> None:
    with pytest.raises(ValueError):
        get_batch(
            _FakeBackend(gate0_counts(shots=100)), shots=100, provenance="precomputed"
        )


def test_batch_response_carries_the_local_result_mapping() -> None:
    response = get_batch(_FakeBackend(gate0_counts(shots=100)), shots=100)
    assert response["result_mapping"] in ("by-name", "by-position")


# ------------------------------------------------------- payload numerics


def test_batch_response_numbers_are_finite() -> None:
    def finite(value):
        if isinstance(value, bool):
            return True
        if isinstance(value, (int, float)):
            return math.isfinite(value)
        if isinstance(value, dict):
            return all(finite(item) for item in value.values())
        if isinstance(value, list):
            return all(finite(item) for item in value)
        return True

    assert finite(get_batch(_FakeBackend(gate0_counts(shots=1000)), shots=1000))


def test_bridge_never_exposes_the_superseded_printed_figure() -> None:
    backend = _FakeBackend(gate0_counts(shots=1000))
    responses = [
        get_batch(backend, shots=1000),
        get_round(backend, probe_kind="MAX_ENTANGLEMENT", shots=1, rng_seed=2),
        get_benchmark(backend, shots=1000, strategy_slug="hurts-max-entanglement"),
        get_benchmark(backend, shots=1000, strategy_slug="hurts-separable"),
        bridge_info(),
    ]
    blob = json.dumps(responses, default=str)
    assert "0.5078125" not in blob


# ------------------------------------------------------- import hygiene


def test_importing_the_bridge_does_not_pull_in_qiskit_aer() -> None:
    script = (
        "import sys; import quantum.bridge as b; "
        "print([m for m in sys.modules if m.startswith('qiskit_aer')])"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip().endswith("[]"), completed.stdout


def test_bridge_module_avoids_novelty_language() -> None:
    forbidden = (
        "we discovered",
        "quantum advantage",
        "quantum computational advantage",
        "breakthrough",
    )
    text = (REPO_ROOT / "quantum/bridge.py").read_text(encoding="utf-8").lower()
    for phrase in forbidden:
        index = text.find(phrase)
        while index >= 0:
            prefix = text[max(0, index - 12) : index]
            assert prefix.rstrip().endswith(("no", "not", "never")), (
                f"bridge contains {phrase!r} (prefix {prefix!r})"
            )
            index = text.find(phrase, index + len(phrase))


# ------------------------------------------------------------ front-end files


def test_index_html_fragment_contract() -> None:
    html = (REPO_ROOT / "index.html").read_text(encoding="utf-8")
    lower = html.lower()
    # Qollab fragment entry (platform injects JS/CSS): no document shell.
    assert "<!doctype" not in lower
    assert "<html>" not in lower and "<html " not in lower
    assert "<head>" not in lower and "<head " not in lower
    assert "<script" not in lower
    # Hero structure survives: one Run control, probe radios, trial control,
    # provenance label; no raw dump.
    assert html.count('id="run"') == 1
    assert 'id="provenance"' in html
    assert "<fieldset" in html and 'type="radio"' in html
    assert 'id="trials"' in html
    # No animation, no external network dependency.
    for banned in ("@keyframes", "animation:", "three.js", "https://", "http://"):
        assert banned not in html, f"index.html must not contain {banned!r}"


def test_main_js_uses_experience_bridge_shape() -> None:
    source = (REPO_ROOT / "main.js").read_text(encoding="utf-8")
    # One-job submission controller: get_experience only.
    assert 'callBridge("get_experience"' in source
    for retired in (
        'callBridge("get_round"',
        'callBridge("get_benchmark"',
        'callBridge("get_batch"',
    ):
        assert retired not in source, f"retired entry still called: {retired}"
    assert "PY.runPython" not in source, "documented shape is ESM + callPromising"
    assert "AerSimulator" not in source, "target is the injected backend"
    # ESM + promising call shape (verified Qollab docs shape).
    assert "callPromising" in source and ".toJs(" in source
    # No duplicate reimplementation of the physics in JavaScript.
    for banned in ("helstrom", "overlap(", "(2 -", "(2-"):
        assert banned.lower() not in source.lower(), (
            f"main.js must not reimplement science: found {banned!r}"
        )


def test_main_css_is_plain_and_offline() -> None:
    css = (REPO_ROOT / "main.css").read_text(encoding="utf-8").lower()
    for banned in ("@keyframes", "animation", "transition", "@import", "url(http"):
        assert banned not in css, f"main.css must not contain {banned!r}"


def test_retired_stylesheets_are_gone() -> None:
    """Qollab loads only root main.css, so no second stylesheet may ship."""
    for relative in ("styles.css", "ui/fingerprint.css"):
        assert not (REPO_ROOT / relative).exists(), (
            f"{relative} must be merged into main.css and deleted"
        )


@pytest.mark.skip(reason="UNVERIFIED EXTERNAL STEP: actual Qollab browser runtime")
def test_actual_qollab_browser_runtime_executes_the_batch() -> None:
    """Step 5 smoke: JS -> Qollab bridge -> Python -> Qiskit -> backend.run -> JS.

    Not executable in this environment: no Qollab/Pyodide runtime is reachable
    from this machine, so the browser path cannot be driven here. The Python
    call shape it wraps is covered by the fake-backend tests above.
    """
    raise AssertionError("Qollab browser runtime is not reachable from this machine")