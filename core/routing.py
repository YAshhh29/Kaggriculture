"""Deterministic shortest-path primitives for the obstacle-free farm grid."""

from __future__ import annotations

from collections.abc import Iterable


Position = tuple[int, int]
Action = list[str]


def distance(origin: Position, target: Position) -> int:
    """Return the exact shortest path length on the farm grid."""
    return abs(origin[0] - target[0]) + abs(origin[1] - target[1])


def step_toward(
    origin: Position,
    target: Position,
    action_at_target: Action,
) -> Action:
    """Take one deterministic shortest-path step or act at the target."""
    if origin == target:
        return action_at_target
    if target[0] < origin[0]:
        return ["WEST"]
    if target[0] > origin[0]:
        return ["EAST"]
    if target[1] < origin[1]:
        return ["NORTH"]
    return ["SOUTH"]


def nearest_position(origin: Position, targets: Iterable[Position]) -> Position:
    """Return the nearest target with stable row-major tie-breaking."""
    return min(
        targets,
        key=lambda target: (distance(origin, target), target[1], target[0]),
    )


def pair_route_cost(
    positions: tuple[Position, Position],
    target: Position,
) -> tuple[int, int]:
    """Rank a paired route by completion time, then total travel."""
    distances = tuple(distance(position, target) for position in positions)
    return max(distances), sum(distances)
