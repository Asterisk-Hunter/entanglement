"""Result types for the flagship one-query engine.

Three shapes, deliberately kept apart so a single literal round can never be
confused with a repeated-trial estimate:

* :class:`RoundResult` - one hidden channel, one guess, one outcome, one flag.
* :class:`StrategyBenchmark` - many trials, an empirical rate with a 95% band,
  and the analytic value and theoretical ceiling kept in separate fields.
* :class:`BatchResult` - the one-batch execution envelope plus its provenance.

Every numeric value carries an explicit kind: `EMPIRICAL`, `ANALYTIC`, or
`THEORETICAL_CEILING`. Provenance is explicit as well; a precomputed result can
never report itself as live.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, Mapping, Tuple

__all__ = [
    "PROBE_KINDS",
    "PROVENANCE_VALUES",
    "VALUE_KINDS",
    "BatchResult",
    "CircuitSpec",
    "Provenance",
    "RoundResult",
    "StrategyBenchmark",
    "success_rate_ci",
]

#: Probe families a strategy can use.
PROBE_KINDS: Tuple[str, ...] = ("SEPARABLE", "MAX_ENTANGLEMENT")

#: The only labels a numeric value may carry.
VALUE_KINDS: Tuple[str, ...] = ("EMPIRICAL", "ANALYTIC", "THEORETICAL_CEILING")


class Provenance:
    """Explicit execution provenance. No implicit or inferred values."""

    LIVE_REMOTE = "live-remote"
    LIVE_LOCAL = "live-local"
    PRECOMPUTED = "precomputed"

    #: Provenance values that represent a real execution in this process.
    LIVE = (LIVE_REMOTE, LIVE_LOCAL)


PROVENANCE_VALUES: Tuple[str, ...] = (
    Provenance.LIVE_REMOTE,
    Provenance.LIVE_LOCAL,
    Provenance.PRECOMPUTED,
)

Outcome = Tuple[Tuple[str, ...], Tuple[str, ...]]


def _require_provenance(provenance: str) -> str:
    if provenance not in PROVENANCE_VALUES:
        raise ValueError(
            f"provenance must be one of {PROVENANCE_VALUES}, got {provenance!r}"
        )
    return provenance


@dataclass(frozen=True)
class CircuitSpec:
    """Local metadata for one circuit in the flagship batch.

    The name and its probe/channel split are kept here so result mapping never
    depends on what a backend chooses to echo back.
    """

    name: str
    probe_kind: str
    channel: str

    def __post_init__(self) -> None:
        if self.probe_kind not in PROBE_KINDS:
            raise ValueError(
                f"probe_kind must be one of {PROBE_KINDS}, got {self.probe_kind!r}"
            )
        if self.channel not in ("A", "B"):
            raise ValueError(f"channel must be 'A' or 'B', got {self.channel!r}")


@dataclass(frozen=True)
class BatchResult:
    """One backend invocation, four circuits, and where it came from."""

    pair_slug: str
    dimension: int
    total_qubits: int
    num_system_qubits: int
    shots: int
    circuits: Tuple[CircuitSpec, ...]
    counts: Mapping[str, Mapping[str, int]]
    outcomes: Mapping[str, Mapping[Outcome, int]]
    provenance: str
    backend_name: str
    result_mapping: str

    def __post_init__(self) -> None:
        _require_provenance(self.provenance)
        if self.result_mapping not in ("by-name", "by-position"):
            raise ValueError(
                "result_mapping must be 'by-name' or 'by-position', got "
                f"{self.result_mapping!r}"
            )
        if self.provenance == Provenance.PRECOMPUTED and self.backend_name not in (
            "precomputed-fixture",
            None,
        ):
            raise ValueError(
                "a precomputed result must not be attributed to a live backend"
            )

    @property
    def is_live(self) -> bool:
        """True only for an execution that really ran here."""
        return self.provenance in Provenance.LIVE

    @property
    def names(self) -> Tuple[str, ...]:
        return tuple(spec.name for spec in self.circuits)

    def counts_for(self, name: str) -> Mapping[str, int]:
        return self.counts[name]

    def outcomes_for(self, name: str) -> Mapping[Outcome, int]:
        return self.outcomes[name]

    def spec_for(self, name: str) -> CircuitSpec:
        for spec in self.circuits:
            if spec.name == name:
                return spec
        raise KeyError(name)

    def probe_kind_for(self, name: str) -> str:
        return self.spec_for(name).probe_kind

    @classmethod
    def from_precomputed(
        cls,
        counts: Mapping[str, Mapping[str, int]],
        shots: int,
        dimension: int,
        total_qubits: int,
        pair_slug: str,
        num_system_qubits: int | None = None,
        circuits: Tuple[CircuitSpec, ...] | None = None,
    ) -> "BatchResult":
        """Build a verified precomputed result. Never attributed to a backend."""
        from quantum.engine import default_circuit_specs, parse_counts

        if num_system_qubits is None:
            num_system_qubits = dimension.bit_length() - 1
        if circuits is None:
            circuits = default_circuit_specs(dimension)
        names = tuple(spec.name for spec in circuits)
        outcomes = {
            name: parse_counts(counts[name], total_qubits, num_system_qubits)
            for name in names
        }
        return cls(
            pair_slug=pair_slug,
            dimension=dimension,
            total_qubits=total_qubits,
            num_system_qubits=num_system_qubits,
            shots=shots,
            circuits=circuits,
            counts={name: dict(counts[name]) for name in names},
            outcomes=outcomes,
            provenance=Provenance.PRECOMPUTED,
            backend_name="precomputed-fixture",
            result_mapping="by-position",
        )

    def to_payload(self) -> dict:
        """JSON-serializable snapshot; no Python proxy types survive."""
        return {
            "kind": "BatchResult",
            "provenance": self.provenance,
            "is_live": self.is_live,
            "backend": self.backend_name,
            "result_mapping": self.result_mapping,
            "pair_slug": self.pair_slug,
            "dimension": self.dimension,
            "total_qubits": self.total_qubits,
            "shots": self.shots,
            "circuits": [
                {
                    "name": spec.name,
                    "probe_kind": spec.probe_kind,
                    "channel": spec.channel,
                }
                for spec in self.circuits
            ],
            "counts": {name: dict(value) for name, value in self.counts.items()},
        }


@dataclass(frozen=True)
class RoundResult:
    """One literal one-query round. No rate, no trials, no probability."""

    hidden_channel: str
    guess: str
    outcome: Outcome
    won: bool

    def to_payload(self) -> dict:
        return {
            "kind": "RoundResult",
            "hidden_channel": self.hidden_channel,
            "guess": self.guess,
            "outcome": [
                "".join(self.outcome[0]),
                "".join(self.outcome[1]),
            ],
            "won": self.won,
        }


@dataclass(frozen=True)
class StrategyBenchmark:
    """Repeated independent one-query trials, reported apart from the theory."""

    pair_slug: str
    strategy_slug: str
    probe_kind: str
    dimension: int
    trials: int
    shots_per_channel: int
    correct_trials: int
    empirical_rate: float
    ci_low: float
    ci_high: float
    analytic_value: float
    ceiling: float
    provenance: str
    bound_kind: str
    empirical_kind: str = "EMPIRICAL"
    analytic_kind: str = "ANALYTIC"
    ceiling_kind: str = "THEORETICAL_CEILING"
    extra: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_provenance(self.provenance)
        for name, value in (
            ("analytic_kind", self.analytic_kind),
            ("ceiling_kind", self.ceiling_kind),
            ("empirical_kind", self.empirical_kind),
            ("bound_kind", self.bound_kind),
        ):
            if value not in VALUE_KINDS:
                raise ValueError(f"{name} must be one of {VALUE_KINDS}, got {value!r}")

    def to_payload(self) -> dict:
        payload = {
            "kind": "StrategyBenchmark",
            "pair_slug": self.pair_slug,
            "strategy_slug": self.strategy_slug,
            "probe_kind": self.probe_kind,
            "dimension": self.dimension,
            "trials": self.trials,
            "shots_per_channel": self.shots_per_channel,
            "correct_trials": self.correct_trials,
            "empirical_rate": self.empirical_rate,
            "empirical_kind": self.empirical_kind,
            "ci_low": self.ci_low,
            "ci_high": self.ci_high,
            "analytic_value": self.analytic_value,
            "analytic_kind": self.analytic_kind,
            "ceiling": self.ceiling,
            "ceiling_kind": self.ceiling_kind,
            "provenance": self.provenance,
            "is_live": self.provenance in Provenance.LIVE,
            "bound_kind": self.bound_kind,
        }
        payload.update(self.extra)
        return payload


def success_rate_ci(correct: int, trials: int, z: float = 1.96) -> Tuple[float, float]:
    """Two-sided 95% interval for a binomial rate (Agresti-Coull).

    Chosen over the plain normal approximation because it stays inside `[0, 1]`
    and remains non-degenerate at a rate of 0 or 1, which the flagship figures
    (a separable rate of exactly 1.0) require.
    """
    if trials <= 0:
        return (0.0, 0.0)
    z2 = z * z
    adjusted = (correct + z2 / 2.0) / (trials + z2)
    margin = z * math.sqrt(adjusted * (1.0 - adjusted) / (trials + z2))
    low = max(0.0, adjusted - margin)
    high = min(1.0, adjusted + margin)
    return (low, high)