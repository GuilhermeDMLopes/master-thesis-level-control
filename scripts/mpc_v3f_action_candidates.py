"""Connected move-based candidate generation for additive MPC V3F.

This module intentionally contains only the action-space kernel. It does not
modify or replace MPC V3/V3E and performs no I/O or real actuation.
"""

from __future__ import annotations

from typing import Iterable, Tuple

DAC_MIN = 0.0
DAC_MAX = 12000.0
MAX_MOVE = 750.0
CANDIDATE_COUNT = 13

# 13 symmetric relative moves. Every move respects MAX_MOVE.
RELATIVE_MOVES: Tuple[float, ...] = (
    -750.0,
    -625.0,
    -500.0,
    -375.0,
    -250.0,
    -125.0,
    0.0,
    125.0,
    250.0,
    375.0,
    500.0,
    625.0,
    750.0,
)


def clamp_dac(value: float) -> float:
    """Clamp a DAC target to the canonical actuator envelope."""
    return min(DAC_MAX, max(DAC_MIN, float(value)))


def connected_candidates(applied_dac: float) -> Tuple[float, ...]:
    """Return connected absolute candidates around current AppliedDAC.

    At interior points there are exactly 13 candidates. Near 0 or 12000,
    clamping can create duplicates; duplicates are removed because evaluating
    the same absolute action multiple times has no optimization value.
    """
    current = clamp_dac(applied_dac)

    values = []
    for move in RELATIVE_MOVES:
        candidate = clamp_dac(current + move)
        if not any(abs(candidate - old) < 1e-12 for old in values):
            values.append(candidate)

    values.sort()
    return tuple(values)


def candidate_moves(applied_dac: float) -> Tuple[float, ...]:
    """Return the actual moves represented by connected_candidates()."""
    current = clamp_dac(applied_dac)
    return tuple(candidate - current for candidate in connected_candidates(current))


def maximum_down_candidate(applied_dac: float) -> float:
    """Lowest legal absolute action at the current AppliedDAC."""
    return min(connected_candidates(applied_dac))


def maximum_up_candidate(applied_dac: float) -> float:
    """Highest legal absolute action at the current AppliedDAC."""
    return max(connected_candidates(applied_dac))


def descent_path_to_zero(start_dac: float) -> Tuple[float, ...]:
    """Construct a deterministic legal path from start_dac to zero.

    This is a topology/reachability proof, not an MPC policy.
    """
    current = clamp_dac(start_dac)
    path = [current]

    for _ in range(100):
        if current <= DAC_MIN + 1e-12:
            return tuple(path)

        nxt = maximum_down_candidate(current)

        if nxt >= current - 1e-12:
            raise RuntimeError(
                f"Candidate graph cannot descend from {current:.3f} DAC."
            )

        if abs(nxt - current) > MAX_MOVE + 1e-12:
            raise RuntimeError("Generated descent move exceeds MAX_MOVE.")

        current = nxt
        path.append(current)

    raise RuntimeError("Descent-to-zero proof exceeded 100 updates.")


def all_moves_within_limit(applied_dac: float) -> bool:
    return all(
        abs(move) <= MAX_MOVE + 1e-12
        for move in candidate_moves(applied_dac)
    )


def has_downward_action(applied_dac: float) -> bool:
    current = clamp_dac(applied_dac)
    return any(candidate < current for candidate in connected_candidates(current))


def has_upward_action(applied_dac: float) -> bool:
    current = clamp_dac(applied_dac)
    return any(candidate > current for candidate in connected_candidates(current))
