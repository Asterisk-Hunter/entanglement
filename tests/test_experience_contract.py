"""Submission-facing contract for the one-job Qollab hero experience."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from quantum.bridge import get_experience  # noqa: E402


class _Header:
    def __init__(self, name: str) -> None:
        self.name = name


class _Data:
    def __init__(self, counts: dict) -> None:
        self.counts = counts


class _Experiment:
    def __init__(self, name: str, counts: dict) -> None:
        self.header = _Header(name)
        self.data = _Data(counts)


class _Result:
    def __init__(self, entries) -> None:
        self.results = [_Experiment(name, counts) for name, counts in entries]

    def get_counts(self, name):
        for experiment in self.results:
            if experiment.header.name == name:
                return experiment.data.counts
        raise KeyError(name)


class _Job:
    def __init__(self, result) -> None:
        self._result = result

    def result(self):
        return self._result


class _Backend:
    name = "selected-qollab-backend"

    def __init__(self) -> None:
        self.run_calls = []

    def run(self, circuits, **kwargs):
        self.run_calls.append((list(circuits), dict(kwargs)))
        by_name = {
            "sep_I": {"0000": kwargs["shots"]},
            "sep_V": {"0001": kwargs["shots"]},
            "me_I": {"0000": kwargs["shots"]},
            "me_V": {"0000": kwargs["shots"]},
        }
        return _Job(_Result([(c.name, by_name[c.name]) for c in circuits]))


def test_submission_experience_uses_one_four_circuit_backend_job() -> None:
    backend = _Backend()
    payload = get_experience(
        backend,
        probe_kind="MAX_ENTANGLEMENT",
        shots=20,
        d=4,
        total_qubits=4,
        rng_seed=7,
    )

    assert len(backend.run_calls) == 1
    circuits, kwargs = backend.run_calls[0]
    assert [circuit.name for circuit in circuits] == [
        "sep_I",
        "sep_V",
        "me_I",
        "me_V",
    ]
    assert kwargs == {"shots": 20}
    assert payload["total_backend_jobs"] == 1
    assert payload["shots_per_channel"] == 20


def test_public_experience_never_leaks_placeholder_live_local_provenance() -> None:
    payload = get_experience(
        _Backend(),
        probe_kind="SEPARABLE",
        shots=5,
        d=4,
        total_qubits=4,
        rng_seed=3,
    )

    assert payload["provenance"] == "qollab-selected-backend"
    assert payload["execution_scope"] == "qollab-selected-backend"
    assert payload["source_label"] == "LIVE QOLLAB SELECTED BACKEND"
    assert payload["is_live"] is True

    assert payload["round"]["provenance"] == "qollab-selected-backend"
    assert payload["round"]["sampled_from_shared_batch"] is True

    for benchmark in payload["benchmarks"].values():
        assert benchmark["provenance"] == "qollab-selected-backend"
        assert benchmark["execution_scope"] == "qollab-selected-backend"
        assert benchmark["source_label"] == "LIVE QOLLAB SELECTED BACKEND"
        assert benchmark["is_live"] is True
        assert benchmark["provenance"] != "live-local"
        assert benchmark["provenance"] != "live-remote"


def test_round_and_benchmarks_share_the_same_execution_scope() -> None:
    payload = get_experience(
        _Backend(),
        probe_kind="MAX_ENTANGLEMENT",
        shots=10,
        d=4,
        total_qubits=4,
        rng_seed=11,
    )

    scopes = {payload["execution_scope"], payload["round"]["execution_scope"]}
    scopes.update(
        benchmark["execution_scope"] for benchmark in payload["benchmarks"].values()
    )
    assert scopes == {"qollab-selected-backend"}
