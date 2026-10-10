"""Extensible quantum channel-pair laboratory.

Import `ChannelPair`, `Strategy`, `load_pair`, and `pair_payload` from here or
from `channels.api`. Add `channels/my_pair.py` implementing `ChannelPair` and it
inherits the same experiment UI, benchmark, claim formatting, and citation
surface with no consumer changes.
"""

from __future__ import annotations

from channels.api import (
    BOUND_KINDS,
    PROBE_KINDS,
    ChannelPair,
    Strategy,
    available_pairs,
    load_pair,
    pair_payload,
)

__all__ = [
    "BOUND_KINDS",
    "PROBE_KINDS",
    "ChannelPair",
    "Strategy",
    "available_pairs",
    "load_pair",
    "pair_payload",
]