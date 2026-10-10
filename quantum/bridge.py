"""Qollab JS/Python bridge for Entanglement Trap.

Qollab's IonQ backends permit one backend job for an entire project Run. The
hero therefore uses :func:`get_experience`: one four-circuit batch is executed
once, then one independent one-query trial is sampled from those results and
both strategy benchmarks are derived from the same job. Later UI clicks only
reveal cached evidence; they never submit another quantum job.

The resource gallery is metadata-only and uses :func:`get_gallery`; it performs
zero backend jobs. Legacy granular entry points remain for local tests and
debugging, but the submission UI must use ``get_experience`` for live evidence.

Scientific/provenance invariant: public Qollab payloads must not guess whether
the selected backend is local or remote. They use the neutral execution scope
``qollab-selected-backend`` unless Qollab exposes a documented discriminator.
"""

from __future__ import annotations

import random
from typing import Dict, Mapping

from channels.api import registered_pair_payloads
from quantum.engine import (
    MAX_LIVE_DIMENSION,
    benchmark_strategy,
    play_one_round,
    run_batch,
)
from quantum.results import PROVENANCE_VALUES, Provenance, RoundResult

__all__ = [
    "BRIDGE_FUNCTIONS",
    "MAX_LIVE_DIMENSION",
    "bridge_info",
    "get_batch",
    "get_benchmark",
    "get_experience",
    "get_gallery",
    "get_round",
]

FLAGSHIP_D = 256
TOTAL_QUBITS = 16
_QOLLAB_SOURCE_LABEL = "LIVE QOLLAB SELECTED BACKEND"
_QOLLAB_EXECUTION_SCOPE = "qollab-selected-backend"


def _require_backend(backend) -> None:
    if backend is None or not hasattr(backend, "run"):
        raise ValueError("a backend with a run() method must be injected")


def _require_shots(shots: int) -> int:
    if not isinstance(shots, int) or isinstance(shots, bool) or shots < 1:
        raise ValueError(f"shots must be a positive integer, got {shots!r}")
    return shots


def _require_provenance(provenance: str) -> str:
    if provenance not in PROVENANCE_VALUES:
        raise ValueError(
            f"provenance must be one of {PROVENANCE_VALUES}, got {provenance!r}"
        )
    return provenance


def _json_round_trip(payload: Dict) -> Dict:
    import json

    if json.loads(json.dumps(payload)) != payload:
        raise ValueError("bridge payload is not JSON-round-trippable")
    return payload


def _as_qollab_live(payload: Dict) -> Dict:
    """Replace internal local/remote guesses with honest public Qollab scope."""
    public = dict(payload)
    public["provenance"] = _QOLLAB_EXECUTION_SCOPE
    public["execution_scope"] = _QOLLAB_EXECUTION_SCOPE
    public["source_label"] = _QOLLAB_SOURCE_LABEL
    public["is_live"] = True
    return public


def _weighted_outcome(outcomes: Mapping, rng: random.Random):
    """Sample one independent one-query outcome from aggregated shot counts."""
    total = sum(int(count) for count in outcomes.values())
    if total < 1:
        raise ValueError("cannot sample a round from an empty result")
    ticket = rng.randrange(total)
    for outcome, count in outcomes.items():
        count = int(count)
        if ticket < count:
            return outcome
        ticket -= count
    raise RuntimeError("weighted outcome selection fell through")


def _round_from_batch(batch, probe_kind: str, rng_seed: int | None) -> RoundResult:
    if probe_kind not in ("SEPARABLE", "MAX_ENTANGLEMENT"):
        raise ValueError(
            "probe_kind must be 'SEPARABLE' or 'MAX_ENTANGLEMENT', "
            f"got {probe_kind!r}"
        )
    rng = random.Random(rng_seed)
    hidden_channel = rng.choice(("A", "B"))
    prefix = "sep" if probe_kind == "SEPARABLE" else "me"
    suffix = "I" if hidden_channel == "A" else "V"
    name = f"{prefix}_{suffix}"
    outcome = _weighted_outcome(batch.outcomes_for(name), rng)
    guess = "A" if outcome[0] == outcome[1] else "B"
    return RoundResult(
        hidden_channel=hidden_channel,
        guess=guess,
        outcome=outcome,
        won=guess == hidden_channel,
    )


def get_experience(
    backend,
    *,
    probe_kind: str,
    shots: int = 100,
    d: int = FLAGSHIP_D,
    total_qubits: int = TOTAL_QUBITS,
    rng_seed: int | None = None,
) -> Dict:
    """Execute the complete hero experience with exactly one backend.run call.

    ``shots`` is the number of independent one-query trials per channel in the
    shared four-circuit batch. The displayed round is one weighted sample from
    the selected probe/channel result, so it remains a one-query outcome while
    the benchmark uses the full independent-trial evidence.

    ``rng_seed`` controls only the deterministic selection of the displayed
    round from already-collected counts. It is never represented as a backend
    execution seed.

    Qollab chooses the backend outside project code and does not expose a stable
    local-vs-remote discriminator in the documented JS/Python bridge contract.
    The submission therefore labels the source honestly as the selected Qollab
    backend rather than guessing LOCAL or REMOTE.

    Live Qollab parsing deliberately ignores measurement noise on padded idle
    qubits. The active probe halves are still parsed exactly; strict padding
    checks remain the default in the engine's audit/test path.
    """
    _require_backend(backend)
    _require_shots(shots)

    batch = run_batch(
        backend,
        shots=shots,
        d=d,
        total_qubits=total_qubits,
        provenance=Provenance.LIVE_LOCAL,
        strict_padding=False,
    )
    round_result = _round_from_batch(batch, probe_kind, rng_seed)

    benchmarks = {}
    for kind, slug in (
        ("SEPARABLE", "hurts-separable"),
        ("MAX_ENTANGLEMENT", "hurts-max-entanglement"),
    ):
        benchmarks[kind] = _as_qollab_live(
            benchmark_strategy(batch, slug).to_payload()
        )

    round_payload = _as_qollab_live(round_result.to_payload())
    round_payload["sampled_from_shared_batch"] = True
    round_payload["round_selection_seed"] = rng_seed

    return _json_round_trip(
        {
            "kind": "ExperienceResult",
            "pair_slug": batch.pair_slug,
            "provenance": _QOLLAB_EXECUTION_SCOPE,
            "source_label": _QOLLAB_SOURCE_LABEL,
            "execution_scope": _QOLLAB_EXECUTION_SCOPE,
            "is_live": True,
            "backend": batch.backend_name,
            "dimension": batch.dimension,
            "shots_per_channel": batch.shots,
            "round_selection_seed": rng_seed,
            "total_backend_jobs": 1,
            "round": round_payload,
            "benchmarks": benchmarks,
        }
    )


def get_gallery(backend=None) -> Dict:
    """Return every registered ChannelPair for the resource lab with zero jobs."""
    del backend
    return _json_round_trip(
        {
            "kind": "GalleryResult",
            "total_backend_jobs": 0,
            "pairs": registered_pair_payloads(),
        }
    )


def get_batch(
    backend,
    shots: int = 1000,
    d: int = FLAGSHIP_D,
    *,
    total_qubits: int = TOTAL_QUBITS,
    provenance: str = Provenance.LIVE_LOCAL,
) -> Dict:
    """Debug/local entry point: run the flagship batch and return its payload."""
    _require_backend(backend)
    _require_shots(shots)
    _require_provenance(provenance)
    batch = run_batch(
        backend,
        shots=shots,
        d=d,
        total_qubits=total_qubits,
        provenance=provenance,
    )
    return _json_round_trip(batch.to_payload())


def get_round(
    backend,
    *,
    probe_kind: str,
    shots: int = 1,
    d: int = FLAGSHIP_D,
    total_qubits: int = TOTAL_QUBITS,
    rng_seed: int | None = None,
) -> Dict:
    """Debug/local entry point for a dedicated literal round.

    The submission UI does not call this because doing so would consume the
    single IonQ job before the strategy benchmark.
    """
    _require_backend(backend)
    _require_shots(shots)
    if shots != 1:
        raise ValueError("a literal round must use exactly one shot")
    round_result = play_one_round(
        backend,
        probe_kind=probe_kind,
        shots=1,
        d=d,
        total_qubits=total_qubits,
        rng_seed=rng_seed,
    )
    payload = dict(round_result.to_payload())
    payload["provenance"] = Provenance.LIVE_LOCAL
    payload["is_live"] = True
    return _json_round_trip(payload)


def get_benchmark(
    backend,
    *,
    strategy_slug: str,
    shots: int = 1000,
    d: int = FLAGSHIP_D,
    total_qubits: int = TOTAL_QUBITS,
    provenance: str = Provenance.LIVE_LOCAL,
) -> Dict:
    """Debug/local entry point for one strategy benchmark."""
    _require_backend(backend)
    _require_shots(shots)
    _require_provenance(provenance)
    batch = run_batch(
        backend,
        shots=shots,
        d=d,
        total_qubits=total_qubits,
        provenance=provenance,
    )
    benchmark = benchmark_strategy(batch, strategy_slug)
    return _json_round_trip(benchmark.to_payload())


def bridge_info() -> Dict:
    """Static description of the bridge surface, for JS-side discovery."""
    return {
        "kind": "BridgeInfo",
        "name": "entanglement-trap-gate0",
        "functions": {
            "get_batch": get_batch,
            "get_round": get_round,
            "get_benchmark": get_benchmark,
            "get_experience": get_experience,
            "get_gallery": get_gallery,
            "bridge_info": bridge_info,
        },
        "flagship_dimension": FLAGSHIP_D,
        "total_qubits": TOTAL_QUBITS,
        "max_live_dimension": MAX_LIVE_DIMENSION,
        "provenance_values": list(PROVENANCE_VALUES),
        "qollab_execution_scope": _QOLLAB_EXECUTION_SCOPE,
        "callable_names": [
            "get_batch",
            "get_round",
            "get_benchmark",
            "get_experience",
            "get_gallery",
            "bridge_info",
        ],
    }


BRIDGE_FUNCTIONS: tuple[str, ...] = (
    "get_batch",
    "get_round",
    "get_benchmark",
    "get_experience",
    "get_gallery",
    "bridge_info",
)
