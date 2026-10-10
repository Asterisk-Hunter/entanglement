"""Release-hardening regressions found during the Sol hostile review.

These are submission-path contracts, not new product features: Qollab runtime
shape, dependency isolation, and one IonQ job for the complete hero experience.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from quantum.bridge import get_experience, get_round  # noqa: E402

TOTAL_QUBITS = 16
N = 8


class _Counts:
    def __init__(self, counts):
        self.counts = counts


class _Header:
    def __init__(self, name):
        self.name = name


class _Experiment:
    def __init__(self, name, counts):
        self.header = _Header(name)
        self.data = _Counts(counts)


class _Result:
    def __init__(self, entries):
        self.results = [_Experiment(name, counts) for name, counts in entries]

    def get_counts(self, name):
        for experiment in self.results:
            if experiment.header.name == name:
                return experiment.data.counts
        raise KeyError(name)


class _Job:
    def __init__(self, result):
        self._result = result

    def result(self):
        return self._result


class _Backend:
    name = "review-fake-backend"

    def __init__(self, counts_by_name):
        self.counts_by_name = counts_by_name
        self.run_calls = []

    def run(self, circuits, **kwargs):
        circuits = list(circuits)
        self.run_calls.append((circuits, dict(kwargs)))
        return _Job(
            _Result([(circuit.name, self.counts_by_name[circuit.name]) for circuit in circuits])
        )


def _key(set_qubits=()):
    chars = ["0"] * TOTAL_QUBITS
    for qubit in set_qubits:
        chars[TOTAL_QUBITS - 1 - qubit] = "1"
    return "".join(chars)


def _counts(shots: int):
    # d=256: overlap^2 = (254/256)^2. A deterministic fixture is enough to
    # exercise the bridge contract; science values are pinned elsewhere.
    agreeing = round(shots * (254 / 256) ** 2)
    disagreeing = shots - agreeing
    me_v = {_key(): agreeing}
    if disagreeing:
        me_v[_key({2 * N - 1})] = disagreeing
    return {
        "sep_I": {_key(): shots},
        "sep_V": {_key({0}): shots},
        "me_I": {_key(): shots},
        "me_V": me_v,
    }


def test_complete_hero_experience_uses_exactly_one_backend_job() -> None:
    backend = _Backend(_counts(100))
    result = get_experience(
        backend,
        probe_kind="MAX_ENTANGLEMENT",
        shots=100,
        rng_seed=7,
    )

    assert len(backend.run_calls) == 1
    circuits, kwargs = backend.run_calls[0]
    assert [circuit.name for circuit in circuits] == ["sep_I", "sep_V", "me_I", "me_V"]
    assert kwargs["shots"] == 100
    assert result["kind"] == "ExperienceResult"
    assert result["total_backend_jobs"] == 1
    assert set(result["benchmarks"]) == {"SEPARABLE", "MAX_ENTANGLEMENT"}
    assert result["round"]["kind"] == "RoundResult"
    assert result["round"]["sampled_from_shared_batch"] is True
    assert json.loads(json.dumps(result)) == result


def test_literal_debug_round_refuses_more_than_one_shot() -> None:
    backend = _Backend(_counts(2))
    with pytest.raises(ValueError, match="exactly one shot"):
        get_round(backend, probe_kind="SEPARABLE", shots=2)
    assert backend.run_calls == []


def test_submission_js_calls_only_the_one_job_experience_entry_point() -> None:
    source = (REPO_ROOT / "main.js").read_text(encoding="utf-8")
    assert 'callBridge("get_experience"' in source
    assert 'callBridge("get_round"' not in source
    assert 'callBridge("get_benchmark"' not in source
    assert 'callBridge("get_batch"' not in source


def test_qollab_js_project_uses_body_fragment_and_root_main_css() -> None:
    html = (REPO_ROOT / "index.html").read_text(encoding="utf-8").lower()
    assert "<html>" not in html and "<html " not in html
    assert "<head>" not in html and "<head " not in html
    assert "<!doctype" not in html
    assert "<link" not in html
    assert "<script" not in html
    assert (REPO_ROOT / "main.css").is_file()


def test_flagship_pair_load_does_not_require_qiskit_aer() -> None:
    """The Qollab flagship must survive when optional Aer is unavailable."""
    script = r'''
import builtins
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
original_import = builtins.__import__
def guarded(name, *args, **kwargs):
    if name == "qiskit_aer" or name.startswith("qiskit_aer."):
        raise AssertionError("flagship path imported qiskit_aer")
    return original_import(name, *args, **kwargs)
builtins.__import__ = guarded
from channels.api import load_pair
pair = load_pair("hurts-identity-v")
assert pair.slug == "hurts-identity-v"
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
    assert completed.stdout.strip() == "ok"
