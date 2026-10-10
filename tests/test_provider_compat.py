"""Provider-compatibility regressions for Qollab/IonQ result handling.

These tests deliberately model two backend behaviours that differ from the
in-memory fake used by the main engine tests:

1. experiment headers omit circuit names but ``Result.get_counts(index)`` still
   provides Qiskit's normalized binary counts;
2. only raw provider data is available and its count keys are hexadecimal.

The production engine must survive both without guessing bit order or exposing
a bound-method string as the backend name.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from quantum.engine import parse_counts, run_batch  # noqa: E402


class _Header:
    name = None


class _Data:
    def __init__(self, counts: dict) -> None:
        self.counts = counts


class _Experiment:
    def __init__(self, counts: dict) -> None:
        self.header = _Header()
        self.data = _Data(counts)


class _IndexedNormalizedResult:
    """Raw data is hex; the public API normalizes by integer index."""

    def __init__(self) -> None:
        self._raw = [
            {"0x0": 1},
            {"0x1": 1},
            {"0x0": 1},
            {"0x0": 1},
        ]
        self._normalized = [
            {"0000": 1},
            {"0001": 1},
            {"0000": 1},
            {"0000": 1},
        ]
        self.results = [_Experiment(counts) for counts in self._raw]
        self.requested = []

    def get_counts(self, experiment):
        self.requested.append(experiment)
        if not isinstance(experiment, int):
            raise KeyError(experiment)
        return self._normalized[experiment]


class _RawHexResult:
    """Compatibility fallback with no get_counts helper at all."""

    def __init__(self) -> None:
        self.results = [
            _Experiment({"0x0": 1}),
            _Experiment({"0x1": 1}),
            _Experiment({"0x0": 1}),
            _Experiment({"0x0": 1}),
        ]


class _Job:
    def __init__(self, result) -> None:
        self._result = result

    def result(self):
        return self._result


class _CallableNameBackend:
    def __init__(self, result) -> None:
        self._result = result
        self.run_calls = 0

    def name(self):
        return "callable-name-backend"

    def run(self, circuits, **kwargs):
        self.run_calls += 1
        assert [circuit.name for circuit in circuits] == [
            "sep_I",
            "sep_V",
            "me_I",
            "me_V",
        ]
        assert kwargs["shots"] == 1
        return _Job(self._result)


def test_positional_results_prefer_qiskit_get_counts_index_normalization() -> None:
    provider_result = _IndexedNormalizedResult()
    backend = _CallableNameBackend(provider_result)

    batch = run_batch(backend, shots=1, d=4, total_qubits=4)

    assert backend.run_calls == 1
    assert batch.result_mapping == "by-position"
    assert batch.backend_name == "callable-name-backend"
    assert provider_result.requested == [0, 1, 2, 3]
    assert batch.counts["sep_I"] == {"0000": 1}
    assert batch.counts["sep_V"] == {"0001": 1}


def test_raw_hex_provider_counts_remain_parseable_as_last_resort() -> None:
    batch = run_batch(
        _CallableNameBackend(_RawHexResult()),
        shots=1,
        d=4,
        total_qubits=4,
    )

    assert batch.result_mapping == "by-position"
    assert batch.counts["sep_V"] == {"0x1": 1}
    assert list(batch.outcomes["sep_V"]) == [
        (("0", "0"), ("0", "1"))
    ]


def test_parse_counts_accepts_documented_prefixed_provider_keys() -> None:
    expected = {(('0',), ('1',)): 3}
    assert parse_counts({"0x1": 3}, total_qubits=2, num_system_qubits=1) == expected
    assert parse_counts({"0b01": 3}, total_qubits=2, num_system_qubits=1) == expected


def test_parse_counts_still_rejects_ambiguous_short_bare_binary_keys() -> None:
    with pytest.raises(ValueError):
        parse_counts({"1": 1}, total_qubits=2, num_system_qubits=1)
