"""Padding policy regressions for the d=64 live fallback."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from quantum.bridge import get_experience  # noqa: E402
from quantum.engine import parse_counts, run_batch  # noqa: E402


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


class _NoisyPaddingBackend:
    name = "noisy-padding-fixture"

    def __init__(self) -> None:
        self.run_calls = []

    def run(self, circuits, **kwargs):
        self.run_calls.append((list(circuits), dict(kwargs)))
        shots = kwargs["shots"]
        # d=64 uses 12 active probe qubits inside the 16-qubit padded register.
        # The four leftmost count bits are idle padding. Flip one of them in
        # every fixture to model readout noise that must not affect the logical
        # discriminator outcome.
        pad_noise = "1000"
        active_zero = "0" * 12
        active_q0 = "0" * 11 + "1"
        counts = {
            "sep_I": {pad_noise + active_zero: shots},
            "sep_V": {pad_noise + active_q0: shots},
            "me_I": {pad_noise + active_zero: shots},
            "me_V": {pad_noise + active_zero: shots},
        }
        return _Job(_Result([(c.name, counts[c.name]) for c in circuits]))


def test_parse_counts_strict_mode_still_rejects_nonzero_padding() -> None:
    key = "1000" + "0" * 12
    with pytest.raises(ValueError, match="padding"):
        parse_counts({key: 1}, total_qubits=16, num_system_qubits=6)


def test_parse_counts_live_mode_ignores_only_idle_padding_bits() -> None:
    key = "1000" + "0" * 11 + "1"
    parsed = parse_counts(
        {key: 3},
        total_qubits=16,
        num_system_qubits=6,
        strict_padding=False,
    )
    outcome = next(iter(parsed))
    assert parsed[outcome] == 3
    half2, half1 = outcome
    assert len(half2) == 6
    assert len(half1) == 6
    assert half1[-1] == "1"


def test_run_batch_default_remains_strict_for_audit_use() -> None:
    with pytest.raises(ValueError, match="padding"):
        run_batch(
            _NoisyPaddingBackend(),
            shots=10,
            d=64,
            total_qubits=16,
        )


def test_qollab_experience_keeps_d64_runnable_with_idle_readout_noise() -> None:
    backend = _NoisyPaddingBackend()
    payload = get_experience(
        backend,
        probe_kind="SEPARABLE",
        shots=10,
        d=64,
        total_qubits=16,
        rng_seed=1,
    )

    assert len(backend.run_calls) == 1
    assert payload["dimension"] == 64
    assert payload["total_backend_jobs"] == 1
    assert payload["benchmarks"]["SEPARABLE"]["empirical_rate"] == 1.0
