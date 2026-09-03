"""Candidate A: guarded calendar recovery and live terminal liquidation."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any

from core.routing import distance, nearest_position, step_toward
from rl.action_space import (
    CropDecision,
    LaborDecision,
    LandDecision,
    MarketDecision,
    RecoveryDecision,
    ResidualAction,
    ServiceDecision,
)
from rl.features import EncodedState
from rl.runtime import (
    AgentAction,
    Baseline,
    ResidualExecutor,
    UnsupportedResidualAction,
    build_residual_agent,
    clone_action,
)


PASS = ["PASS"]
MOVE_ACTIONS = {"NORTH", "SOUTH", "EAST", "WEST"}
FINAL_EXECUTABLE_STEP = 718
TERMINAL_PLANNING_STEP = 700
TERMINAL_RETURN_STEP = 716
TERMINAL_SELL_STEP = 717
SHED_CAPACITY = 100
SELLABLE_PRODUCTS = (
    "MELON",
    "MILK",
    "WOOL",
    "STRAWBERRY",
    "TOMATO",
    "CARROT",
    "EGG",
    "WHEAT",
    "FERTILIZER",
)
ANIMAL_STRUCTURES = {
    "GOOSE": "COOP",
    "COW": "PASTURE",
    "SHEEP": "PASTURE",
}
RECOVERABLE_SETUP = {"PLANT", "BUILD_COOP", "BUILD_PASTURE"}
LOCKED_TILE_OPERATIONS = {
    "PLANT",
    "WATER",
    "HARVEST",
    "FERTILIZE",
    "DIG",
    "BUILD_COOP",
    "BUILD_PASTURE",
    "FEED",
    "CARE",
    "COLLECT_FERTILIZER",
}


@dataclass(frozen=True)
class PendingRepair:
    position: tuple[int, int]
    action: tuple[Any, ...]
    expires_step: int


@dataclass
class TerminalCommitment:
    target: tuple[int, int]
    shed: tuple[int, int]
    needs_water: bool
    phase: str = "target"


@dataclass
class EpisodeRecovery:
    last_step: int = -1
    pending: dict[int, PendingRepair] = field(default_factory=dict)
    terminal: dict[int, TerminalCommitment] = field(default_factory=dict)


@dataclass(frozen=True)
class GuardEvent:
    guard_type: str
    worker: int
    step: int
    original_action: tuple[Any, ...]
    replacement_action: tuple[Any, ...]
    detail: str = ""


@dataclass
class CandidateATelemetry:
    """Structured residual counters for benchmark output only."""

    events: list[GuardEvent] = field(default_factory=list)
    prevented_invalid: int = 0
    recovered_units: int = 0
    sold_units: int = 0
    terminal_inventory_before: dict[str, int] = field(default_factory=dict)
    terminal_inventory_after: dict[str, int] = field(default_factory=dict)

    def record(
        self,
        *,
        guard_type: str,
        worker: int,
        step: int,
        original: list[Any],
        replacement: list[Any],
        detail: str = "",
    ) -> None:
        if original == replacement:
            return
        self.events.append(
            GuardEvent(
                guard_type=guard_type,
                worker=worker,
                step=step,
                original_action=tuple(original),
                replacement_action=tuple(replacement),
                detail=detail,
            )
        )

    def summarize(self) -> dict[str, Any]:
        by_guard: dict[str, int] = {}
        for event in self.events:
            by_guard[event.guard_type] = by_guard.get(event.guard_type, 0) + 1
        return {
            "guard_firings": len(self.events),
            "guard_types": by_guard,
            "prevented_invalid": self.prevented_invalid,
            "recovered_units": self.recovered_units,
            "sold_units": self.sold_units,
            "terminal_inventory_before": dict(self.terminal_inventory_before),
            "terminal_inventory_after": dict(self.terminal_inventory_after),
            "events": [
                {
                    "guard_type": event.guard_type,
                    "worker": event.worker,
                    "step": event.step,
                    "original_action": list(event.original_action),
                    "replacement_action": list(event.replacement_action),
                    "detail": event.detail,
                }
                for event in self.events
            ],
        }


class CandidateAPolicy:
    """Enable only the deterministic Candidate A residual Options."""

    def __init__(
        self,
        *,
        enable_recovery: bool = True,
        enable_liquidation: bool = True,
        enable_terminal_commitments: bool = True,
    ) -> None:
        self._enable_recovery = enable_recovery
        self._enable_liquidation = enable_liquidation
        self._terminal_start = (
            TERMINAL_PLANNING_STEP
            if enable_terminal_commitments
            else TERMINAL_RETURN_STEP
        )

    def select_action(self, state: EncodedState) -> ResidualAction:
        features = state.as_dict()
        step = round(features["episode_fraction"] * FINAL_EXECUTABLE_STEP)
        market = (
            MarketDecision.LIQUIDATE
            if self._enable_liquidation and step >= self._terminal_start
            else MarketDecision.KEEP
        )
        return ResidualAction(
            market=market,
            recovery=(
                RecoveryDecision.REPAIR_STATE_DRIFT
                if self._enable_recovery
                else RecoveryDecision.KEEP
            ),
        )


class CandidateAExecutor(ResidualExecutor):
    """Apply narrow recovery and liquidation without replacing strategy."""

    def __init__(
        self,
        baseline: Baseline,
        *,
        telemetry: CandidateATelemetry | None = None,
    ) -> None:
        self._baseline = baseline
        self._telemetry = telemetry
        self._episodes: dict[int, EpisodeRecovery] = {}

    def apply(
        self,
        observation: dict[str, Any],
        baseline_action: AgentAction,
        residual_action: ResidualAction,
    ) -> AgentAction:
        self._require_supported(residual_action)
        action = clone_action(baseline_action)
        player = int(observation["player"])
        step = int(observation.get("step", 0))
        episode = self._episode(player, step)
        if residual_action.recovery == RecoveryDecision.REPAIR_STATE_DRIFT:
            action = self._repair_units(observation, action, episode)
        if residual_action.market == MarketDecision.LIQUIDATE:
            action = self._terminal_units(observation, action, episode)
            if step >= TERMINAL_SELL_STEP:
                before = _shed_inventory(observation)
                market = self._terminal_market(observation, action)
                after = _projected_shed_after_market(before, market)
                if self._telemetry is not None:
                    self._telemetry.terminal_inventory_before = before
                    self._telemetry.terminal_inventory_after = after
                    self._telemetry.sold_units += sum(
                        int(order[2])
                        for order in market
                        if len(order) >= 3 and str(order[0]) == "SELL"
                    )
                action["market"] = market
        episode.last_step = step
        return action

    def _require_supported(self, action: ResidualAction) -> None:
        unsupported = (
            action.labor != LaborDecision.KEEP
            or action.land != LandDecision.KEEP
            or action.crop != CropDecision.KEEP
            or action.service != ServiceDecision.KEEP
            or action.market
            not in {MarketDecision.KEEP, MarketDecision.LIQUIDATE}
            or action.recovery
            not in {
                RecoveryDecision.KEEP,
                RecoveryDecision.REPAIR_STATE_DRIFT,
            }
        )
        if unsupported:
            raise UnsupportedResidualAction(
                f"Candidate A cannot execute {action!r}"
            )

    def _episode(self, player: int, step: int) -> EpisodeRecovery:
        episode = self._episodes.setdefault(player, EpisodeRecovery())
        if step == 0 or step <= episode.last_step:
            episode = EpisodeRecovery()
            self._episodes[player] = episode
        return episode

    def _repair_units(
        self,
        observation: dict[str, Any],
        action: AgentAction,
        episode: EpisodeRecovery,
    ) -> AgentAction:
        player = int(observation["player"])
        step = int(observation.get("step", 0))
        farm = observation["farms"][player]
        positions = [
            tuple(farm["farmer"]),
            *(tuple(position) for position in farm.get("hands", [])),
        ]
        baseline_planned = [
            action.get("farmer", PASS),
            *action.get("hands", []),
        ]
        planned = [
            list(baseline_planned[worker])
            if worker < len(baseline_planned)
            else list(PASS)
            for worker in range(len(positions))
        ]
        for worker in range(len(positions), len(baseline_planned)):
            if self._telemetry is not None:
                stale = list(baseline_planned[worker])
                self._telemetry.record(
                    guard_type="hand_align",
                    worker=worker,
                    step=step,
                    original=stale,
                    replacement=list(PASS),
                    detail="dropped_stale_calendar_hand",
                )
                self._telemetry.prevented_invalid += 1
        for worker, position in enumerate(positions):
            pending = episode.pending.get(worker)
            if pending is not None:
                replacement = self._continue_repair(
                    observation,
                    worker,
                    position,
                    pending,
                )
                if replacement is not None:
                    original = list(planned[worker])
                    planned[worker] = replacement
                    if self._telemetry is not None:
                        self._telemetry.record(
                            guard_type="pending_repair",
                            worker=worker,
                            step=step,
                            original=original,
                            replacement=replacement,
                            detail="continue",
                        )
                    if replacement[0] == "PLANT":
                        episode.pending[worker] = PendingRepair(
                            position=position,
                            action=("WATER",),
                            expires_step=step + 1,
                        )
                    else:
                        episode.pending.pop(worker, None)
                    continue
                if self._telemetry is not None:
                    self._telemetry.record(
                        guard_type="pending_repair",
                        worker=worker,
                        step=step,
                        original=list(planned[worker]),
                        replacement=list(planned[worker]),
                        detail="cancelled",
                    )
                episode.pending.pop(worker, None)
            tile = _tile_at(farm, position)
            operation = str(planned[worker][0]) if planned[worker] else "PASS"
            if (
                operation in RECOVERABLE_SETUP
                and _is_weed(tile)
                and _repair_has_time(observation, operation)
                and self._repair_preserves_schedule(
                    observation,
                    worker,
                    operation,
                )
            ):
                original = list(planned[worker])
                episode.pending[worker] = PendingRepair(
                    position=position,
                    action=tuple(original),
                    expires_step=step + (2 if operation == "PLANT" else 1),
                )
                planned[worker] = ["DIG"]
                if self._telemetry is not None:
                    self._telemetry.record(
                        guard_type="weed_dig",
                        worker=worker,
                        step=step,
                        original=original,
                        replacement=["DIG"],
                    )
                    self._telemetry.recovered_units += 1
            elif operation in LOCKED_TILE_OPERATIONS and _is_locked(tile):
                original = list(planned[worker])
                planned[worker] = list(PASS)
                if self._telemetry is not None:
                    self._telemetry.record(
                        guard_type="locked_quadrant",
                        worker=worker,
                        step=step,
                        original=original,
                        replacement=list(PASS),
                        detail="calendar_targeted_unpurchased_land",
                    )
                    self._telemetry.prevented_invalid += 1
            elif (
                operation in LOCKED_TILE_OPERATIONS
                and operation != "DIG"
                and _is_weed(tile)
            ):
                # The repair above only fires for RECOVERABLE_SETUP work that
                # also passes the schedule-safety check, so most weed-blocked
                # actions still reach the simulator as guaranteed no-ops -- a
                # real-game audit found 37 of them across three games (WATER,
                # HARVEST and FERTILIZE on WEED, plus PLANT the repair
                # declined). None of those operations can act on a weed, so
                # the turn is already lost; clearing the weed in place is
                # strictly better than spending it on nothing.
                #
                # This is a 1:1 substitution, never an inserted step: the
                # worker does not move either way, so it cannot displace the
                # calendar's later scheduled movement -- the failure mode that
                # made the original broad multi-step recovery cost -32690 in
                # section 6. No retry is queued for the same reason.
                original = list(planned[worker])
                planned[worker] = ["DIG"]
                if self._telemetry is not None:
                    self._telemetry.record(
                        guard_type="weed_clear",
                        worker=worker,
                        step=step,
                        original=original,
                        replacement=["DIG"],
                        detail="doomed_action_on_weed_cleared_in_place",
                    )
                    self._telemetry.prevented_invalid += 1
        return {
            "farmer": planned[0],
            "hands": planned[1:],
            "market": [list(order) for order in action.get("market", [])],
        }

    def _repair_preserves_schedule(
        self,
        observation: dict[str, Any],
        worker: int,
        operation: str,
    ) -> bool:
        next_action = self._future_action(observation, worker, 1)
        if operation == "PLANT":
            return (
                next_action == ["WATER"]
                and self._future_action(observation, worker, 2) == PASS
            )
        return next_action == PASS

    def _future_action(
        self,
        observation: dict[str, Any],
        worker: int,
        offset: int,
    ) -> list[Any] | None:
        future = copy.deepcopy(observation)
        step = int(observation.get("step", 0)) + offset
        future["step"] = step
        future["day"] = step // 24
        future["hour"] = step % 24
        action = self._baseline(future)
        actions = [action.get("farmer", PASS), *action.get("hands", [])]
        if worker >= len(actions):
            return None
        worker_action = actions[worker]
        return list(worker_action) if isinstance(worker_action, list) else None

    def _continue_repair(
        self,
        observation: dict[str, Any],
        worker: int,
        position: tuple[int, int],
        pending: PendingRepair,
    ) -> list[Any] | None:
        step = int(observation.get("step", 0))
        if step > pending.expires_step or position != pending.position:
            return None
        player = int(observation["player"])
        farm = observation["farms"][player]
        private = observation["private"]
        tile = _tile_at(farm, position)
        operation = str(pending.action[0])
        if operation == "PLANT":
            crop = str(pending.action[1])
            if tile is None and int(private["seeds"].get(crop, 0)) > 0:
                return list(pending.action)
            return None
        if operation in {"BUILD_COOP", "BUILD_PASTURE"}:
            return list(pending.action) if tile is None else None
        if operation == "WATER":
            if (
                isinstance(tile, dict)
                and tile.get("kind") == "PLANT"
                and not tile.get("watered_today", False)
            ):
                return ["WATER"]
        return None

    def _terminal_units(
        self,
        observation: dict[str, Any],
        action: AgentAction,
        episode: EpisodeRecovery,
    ) -> AgentAction:
        player = int(observation["player"])
        step = int(observation.get("step", 0))
        farm = observation["farms"][player]
        private = observation["private"]
        positions = [
            tuple(farm["farmer"]),
            *(tuple(position) for position in farm.get("hands", [])),
        ]
        planned = [action["farmer"], *action["hands"]]
        shed_tiles = _shed_access_tiles(len(farm["tiles"]))
        transitions = FINAL_EXECUTABLE_STEP - step + 1
        reserved = {
            commitment.target for commitment in episode.terminal.values()
        }
        for worker, position in enumerate(positions):
            commitment = episode.terminal.get(worker)
            if commitment is None and step < TERMINAL_RETURN_STEP:
                commitment = self._find_terminal_commitment(
                    observation,
                    worker,
                    position,
                    reserved,
                )
                if commitment is not None:
                    episode.terminal[worker] = commitment
                    reserved.add(commitment.target)
                    if self._telemetry is not None:
                        self._telemetry.record(
                            guard_type="terminal_commitment",
                            worker=worker,
                            step=step,
                            original=list(planned[worker]),
                            replacement=list(planned[worker]),
                            detail="started",
                        )
            if commitment is None:
                continue
            original = list(planned[worker])
            replacement = self._follow_terminal_commitment(
                observation,
                worker,
                position,
                commitment,
            )
            if replacement is None:
                if self._telemetry is not None:
                    self._telemetry.record(
                        guard_type="terminal_commitment",
                        worker=worker,
                        step=step,
                        original=original,
                        replacement=original,
                        detail="cancelled",
                    )
                episode.terminal.pop(worker, None)
                continue
            planned[worker] = replacement
            if self._telemetry is not None:
                self._telemetry.record(
                    guard_type="terminal_commitment",
                    worker=worker,
                    step=step,
                    original=original,
                    replacement=replacement,
                    detail=commitment.phase,
                )
        if step < TERMINAL_RETURN_STEP:
            return {
                "farmer": planned[0],
                "hands": planned[1:],
                "market": action["market"],
            }
        for worker, position in enumerate(positions):
            if worker in episode.terminal:
                continue
            inventory = _inventory(private, worker)
            if _sellable_units(inventory) > 0:
                original = list(planned[worker])
                if position in shed_tiles:
                    planned[worker] = ["DROP"]
                    if self._telemetry is not None:
                        self._telemetry.record(
                            guard_type="terminal_inventory_route",
                            worker=worker,
                            step=step,
                            original=original,
                            replacement=["DROP"],
                        )
                    continue
                target = nearest_position(position, shed_tiles)
                if distance(position, target) + 1 <= transitions:
                    replacement = step_toward(position, target, ["DROP"])
                    planned[worker] = replacement
                    if self._telemetry is not None:
                        self._telemetry.record(
                            guard_type="terminal_inventory_route",
                            worker=worker,
                            step=step,
                            original=original,
                            replacement=replacement,
                        )
                    continue
            tile = _tile_at(farm, position)
            if _harvestable(tile):
                return_distance = min(
                    distance(position, target) for target in shed_tiles
                )
                if return_distance + 2 <= transitions:
                    original = list(planned[worker])
                    planned[worker] = ["HARVEST"]
                    if self._telemetry is not None:
                        self._telemetry.record(
                            guard_type="terminal_inventory_route",
                            worker=worker,
                            step=step,
                            original=original,
                            replacement=["HARVEST"],
                        )
        return {
            "farmer": planned[0],
            "hands": planned[1:],
            "market": action["market"],
        }

    def _find_terminal_commitment(
        self,
        observation: dict[str, Any],
        worker: int,
        position: tuple[int, int],
        reserved: set[tuple[int, int]],
    ) -> TerminalCommitment | None:
        step = int(observation.get("step", 0))
        if step < TERMINAL_PLANNING_STEP:
            return None
        player = int(observation["player"])
        farm = observation["farms"][player]
        board_size = len(farm["tiles"])
        future_position = position
        trace: list[tuple[int, list[Any], tuple[int, int]]] = []
        harvest_step = None
        target = None
        for offset in range(FINAL_EXECUTABLE_STEP - step + 1):
            worker_action = self._future_action(observation, worker, offset)
            if not worker_action:
                return None
            operation = str(worker_action[0])
            trace.append((step + offset, worker_action, future_position))
            if operation == "HARVEST":
                target = future_position
                harvest_step = step + offset
                break
            future_position = _moved(
                future_position,
                operation,
                board_size,
            )
        if target is None or harvest_step is None or target in reserved:
            return None
        tile = _tile_at(farm, target)
        if not (
            isinstance(tile, dict)
            and tile.get("kind") == "PLANT"
            and int(tile.get("yield_units", 0)) > 0
        ):
            return None
        needs_water = False
        for _, worker_action, action_position in trace[:-1]:
            operation = str(worker_action[0])
            if operation in MOVE_ACTIONS or operation in {"PASS", "DROP"}:
                continue
            if operation == "WATER" and action_position == target:
                needs_water = not bool(tile.get("watered_today", False))
                continue
            return None
        shed_tiles = _shed_access_tiles(board_size)
        shed = nearest_position(target, shed_tiles)
        baseline_return = distance(target, shed) + 1
        if baseline_return <= FINAL_EXECUTABLE_STEP - harvest_step:
            return None
        required = (
            distance(position, target)
            + int(needs_water)
            + 1
            + distance(target, shed)
            + 1
        )
        available = FINAL_EXECUTABLE_STEP - step + 1
        if required > available or required < available - 1:
            return None
        return TerminalCommitment(
            target=target,
            shed=shed,
            needs_water=needs_water,
        )

    def _follow_terminal_commitment(
        self,
        observation: dict[str, Any],
        worker: int,
        position: tuple[int, int],
        commitment: TerminalCommitment,
    ) -> list[Any] | None:
        player = int(observation["player"])
        farm = observation["farms"][player]
        private = observation["private"]
        if commitment.phase == "target":
            if position != commitment.target:
                return step_toward(position, commitment.target, PASS)
            tile = _tile_at(farm, position)
            if commitment.needs_water:
                if not (
                    isinstance(tile, dict)
                    and tile.get("kind") == "PLANT"
                    and not tile.get("watered_today", False)
                ):
                    return None
                commitment.needs_water = False
                return ["WATER"]
            if not _harvestable(tile):
                return None
            commitment.phase = "shed"
            return ["HARVEST"]
        inventory = _inventory(private, worker)
        if _sellable_units(inventory) <= 0:
            return None
        if position == commitment.shed:
            return ["DROP"]
        return step_toward(position, commitment.shed, ["DROP"])

    def _terminal_market(
        self,
        observation: dict[str, Any],
        action: AgentAction,
    ) -> list[list[Any]]:
        projected = _projected_shed(observation, action)
        return [
            ["SELL", product, int(projected.get(product, 0))]
            for product in SELLABLE_PRODUCTS
            if int(projected.get(product, 0)) > 0
        ]


def _tile_at(farm: dict[str, Any], position: tuple[int, int]) -> Any:
    x, y = position
    return farm["tiles"][y][x]


def _is_weed(tile: Any) -> bool:
    return isinstance(tile, dict) and tile.get("kind") == "WEED"


def _is_locked(tile: Any) -> bool:
    return tile == "LOCKED"


def _repair_has_time(observation: dict[str, Any], operation: str) -> bool:
    day = int(observation.get("day", 0))
    hour = int(observation.get("hour", 0))
    if day >= 29:
        return False
    return hour <= (21 if operation == "PLANT" else 22)


def _moved(
    position: tuple[int, int],
    operation: str,
    board_size: int,
) -> tuple[int, int]:
    offsets = {
        "NORTH": (0, -1),
        "SOUTH": (0, 1),
        "EAST": (1, 0),
        "WEST": (-1, 0),
    }
    if operation not in offsets:
        return position
    dx, dy = offsets[operation]
    target = (position[0] + dx, position[1] + dy)
    if 0 <= target[0] < board_size and 0 <= target[1] < board_size:
        return target
    return position


def _inventory(private: dict[str, Any], worker: int) -> dict[str, Any]:
    inventories = private.get("inventories", [])
    if worker < len(inventories) and isinstance(inventories[worker], dict):
        return inventories[worker]
    return {}


def _shed_access_tiles(board_size: int) -> tuple[tuple[int, int], ...]:
    half = board_size // 2
    return (
        (half - 1, half - 1),
        (half, half - 1),
        (half - 1, half),
        (half, half),
    )


def _sellable_units(inventory: dict[str, Any]) -> int:
    return sum(int(inventory.get(product, 0)) for product in SELLABLE_PRODUCTS)


def _harvestable(tile: Any) -> bool:
    return isinstance(tile, dict) and int(tile.get("yield_units", 0)) > 0


def _projected_shed(
    observation: dict[str, Any],
    action: AgentAction,
) -> dict[str, int]:
    player = int(observation["player"])
    farm = observation["farms"][player]
    private = observation["private"]
    shed = {
        str(item): int(quantity)
        for item, quantity in private.get("shed", {}).items()
    }
    positions = [
        tuple(farm["farmer"]),
        *(tuple(position) for position in farm.get("hands", [])),
    ]
    actions = [action["farmer"], *action["hands"]]
    shed_tiles = set(_shed_access_tiles(len(farm["tiles"])))
    for worker, (position, worker_action) in enumerate(
        zip(positions, actions, strict=True)
    ):
        if not worker_action:
            continue
        inventory = _inventory(private, worker)
        operation = str(worker_action[0])
        if operation == "DROP" and position in shed_tiles:
            for item, quantity in inventory.items():
                room = max(0, SHED_CAPACITY - sum(shed.values()))
                deposited = min(max(0, int(quantity)), room)
                if deposited > 0:
                    shed[str(item)] = shed.get(str(item), 0) + deposited
            continue
        if operation != "PLACE" or len(worker_action) < 2:
            continue
        item = str(worker_action[1])
        tile = _tile_at(farm, position)
        if (
            item in ANIMAL_STRUCTURES
            and isinstance(tile, dict)
            and tile.get("kind") == ANIMAL_STRUCTURES[item]
            and not tile.get("animal")
        ):
            continue
        if position not in shed_tiles:
            continue
        requested = int(worker_action[2]) if len(worker_action) >= 3 else 1
        room = max(0, SHED_CAPACITY - sum(shed.values()))
        deposited = min(max(0, requested), int(inventory.get(item, 0)), room)
        if deposited > 0:
            shed[item] = shed.get(item, 0) + deposited
    return shed


def _shed_inventory(observation: dict[str, Any]) -> dict[str, int]:
    private = observation["private"]
    return {
        str(item): int(quantity)
        for item, quantity in private.get("shed", {}).items()
        if int(quantity) > 0
    }


def _projected_shed_after_market(
    before: dict[str, int],
    market: list[list[Any]],
) -> dict[str, int]:
    after = dict(before)
    for order in market:
        if len(order) < 3 or str(order[0]) != "SELL":
            continue
        product = str(order[1])
        sold = int(order[2])
        if sold <= 0:
            continue
        remaining = max(0, after.get(product, 0) - sold)
        if remaining:
            after[product] = remaining
        else:
            after.pop(product, None)
    return after


def build_candidate_a_agent(
    *,
    baseline: Baseline,
    enable_recovery: bool = True,
    enable_liquidation: bool = True,
    enable_terminal_commitments: bool = True,
    telemetry: CandidateATelemetry | None = None,
) -> Baseline:
    executor = CandidateAExecutor(baseline, telemetry=telemetry)
    return build_residual_agent(
        CandidateAPolicy(
            enable_recovery=enable_recovery,
            enable_liquidation=enable_liquidation,
            enable_terminal_commitments=enable_terminal_commitments,
        ),
        baseline=baseline,
        executor=executor,
    )
