"""Turn a frozen route's dead actions into work, without moving anybody.

A tape's action was recorded against a farm state that no longer exists.
When the state has diverged the simulator silently refuses the action and
the worker-turn is gone. Measured over three games, Candidate F's route
loses about 146 worker-turns a game this way and Candidate D's about 284
-- overwhelmingly PLACE on a pen that is already occupied or with no
animal in hand, plus a scatter of WATER on a tile that is no longer a
plant.

Those turns look free -- a refused action produces nothing at all -- but
**substituting for them measured badly and the layer is switched off in
Candidate F.** On 80 games against real opponents it took the win rate
from 90% to 41%, and isolating the substitutions one at a time showed why:
replacing refused `PLACE` actions costs about four animals a game, because
the refusal test has a small false-positive rate and a mis-flagged `PLACE`
is a placement that never happens. `HARVEST`-only substitution measured
neutral; every set including `COLLECT_FERTILIZER` lost 23,000 coins.

The module is kept because `would_be_refused` is an accurate and useful
diagnostic on its own -- it is what measured the 146-turn figure above,
and it is the right starting point if anyone wants to make the
substitution safe. Making it safe means proving the false positives away,
most likely by reconciling the action list against `farm["hands"]` when a
hand is hired mid-turn, which is where the ordering can slip.

**The safety rule is that a substitute must act on the tile the worker is
already standing on.** A tape's later actions assume its workers are where
its recording left them, so moving one -- even toward something valuable
-- desynchronises everything that follows. In-place substitution cannot:
the worker ends the turn exactly where the route expects it.

The substitutes are also restricted to actions that cannot take anything
the route is relying on:

* CARE and COLLECT_FERTILIZER need no inventory and destroy nothing;
* HARVEST **only on an animal**, which keeps producing afterwards -- never
  on a plant, because the simulator destroys a non-ongoing crop when it is
  picked, so an early harvest would throw away the yield the route was
  waiting for;
* WATER on a plant that has not been watered today, which only ever adds
  yield;
* DIG on a weed, which clears ground the route may want.

Deliberately excluded: PLANT and PICKUP (would consume seed or shed stock
the route has budgeted), DROP (changes carried inventory the route depends
on), and BUILD (changes the shape of the board).
"""

from __future__ import annotations

from typing import Any

from rl.runtime import AgentAction, Baseline, clone_action

MOVES = frozenset({"NORTH", "SOUTH", "EAST", "WEST"})
SHED_TILES = frozenset({(4, 4), (5, 4), (4, 5), (5, 5)})
CROP_FIRST_YIELD = {
    "WHEAT": 2, "CARROT": 2, "TOMATO": 8, "STRAWBERRY": 10, "MELON": 10,
}
STRUCTURE_OF = {"COW": "PASTURE", "SHEEP": "PASTURE", "GOOSE": "COOP"}


def _shed_adjacent(x: int, y: int) -> bool:
    return any(abs(x - sx) + abs(y - sy) <= 1 for sx, sy in SHED_TILES)


def would_be_refused(
    action: list[Any],
    tile: Any,
    inventory: dict[str, int],
    seeds: dict[str, int],
    shed: dict[str, int],
    day: int,
    x: int,
    y: int,
    inventory_known: bool = True,
) -> bool:
    """Will the simulator refuse this action outright in this state?

    Mirrors the guard clauses in _apply_unit_action. Movement and PASS are
    never counted as refused: a move is always spent legitimately, and a
    PASS is a choice the route made rather than a failure.

    `inventory_known` is load-bearing and was learned the hard way. Hands
    are hired during a turn, and a hand hired this turn has no entry in
    `private["inventories"]` yet -- so reading its inventory yields an
    empty dict. Treating that as fact made every `PLACE` by a fresh hand
    look refused, and the layer then overwrote *valid* placements: the
    herd fell from fourteen animals to ten and the win rate from 90% to
    41%. When the inventory cannot be read, the checks that depend on it
    must answer "not refused", because a substitution is only ever safe
    when the original action is certainly dead.
    """
    if not action:
        return False
    op = str(action[0])
    if op in MOVES or op == "PASS":
        return False
    entry = tile if isinstance(tile, dict) else None

    if op == "WATER":
        return not (entry and entry.get("kind") == "PLANT"
                    and not entry.get("watered_today"))
    if op == "HARVEST":
        if not (entry and int(entry.get("yield_units", 0)) > 0):
            return True
        if entry.get("kind") == "PLANT":
            first = CROP_FIRST_YIELD.get(str(entry.get("crop")), 0)
            return day - int(entry.get("planted_day", day)) < first
        return False
    if op == "PLANT":
        crop = str(action[1]) if len(action) > 1 else ""
        return tile is not None or int(seeds.get(crop, 0)) <= 0
    if op == "FEED":
        if not (entry and "animal" in entry and not entry.get("fed_today")):
            return True
        return inventory_known and int(inventory.get("WHEAT", 0)) <= 0
    if op == "CARE":
        return not (entry and "animal" in entry
                    and not entry.get("cared_today"))
    if op == "COLLECT_FERTILIZER":
        return not (entry and "animal" in entry
                    and entry.get("fertilizer_available"))
    if op == "FERTILIZE":
        if not (entry and entry.get("kind") == "PLANT"):
            return True
        return inventory_known and int(inventory.get("FERTILIZER", 0)) <= 0
    if op == "DIG":
        return not (entry and entry.get("kind") == "WEED")
    if op in ("BUILD_PASTURE", "BUILD_COOP"):
        return tile is not None
    if op == "PICKUP":
        item = str(action[1]) if len(action) > 1 else ""
        return not (_shed_adjacent(x, y) and int(shed.get(item, 0)) > 0)
    if op == "DROP":
        if not _shed_adjacent(x, y):
            return True
        return inventory_known and not any(
            int(v) > 0 for v in inventory.values()
        )
    if op == "PLACE":
        item = str(action[1]) if len(action) > 1 else ""
        # Tile evidence alone is decisive here: a pen that is occupied, or
        # is the wrong kind, refuses the placement whatever is in hand.
        if not (entry and entry.get("kind") == STRUCTURE_OF.get(item)
                and "animal" not in entry):
            return True
        return inventory_known and int(inventory.get(item, 0)) <= 0
    return False


ALLOWED_OPS = frozenset(
    {"COLLECT_FERTILIZER", "HARVEST", "CARE", "FEED", "WATER", "DIG"}
)


def rescue_action(
    tile: Any,
    inventory: dict[str, int],
    day: int,
    allowed: frozenset[str] = ALLOWED_OPS,
) -> list[Any] | None:
    """The best legal in-place action here, or None if there is none."""
    entry = tile if isinstance(tile, dict) else None
    if entry is None:
        return None
    if "animal" in entry:
        if entry.get("fertilizer_available") and "COLLECT_FERTILIZER" in allowed:
            return ["COLLECT_FERTILIZER"]
        if int(entry.get("yield_units", 0)) > 0 and "HARVEST" in allowed:
            return ["HARVEST"]
        if not entry.get("cared_today") and "CARE" in allowed:
            return ["CARE"]
        if (not entry.get("fed_today") and "FEED" in allowed
                and int(inventory.get("WHEAT", 0)) > 0):
            return ["FEED"]
        return None
    if (entry.get("kind") == "PLANT" and not entry.get("watered_today")
            and "WATER" in allowed):
        return ["WATER"]
    if entry.get("kind") == "WEED" and "DIG" in allowed:
        return ["DIG"]
    return None


def _positions(farm: dict[str, Any]) -> list[tuple[int, int]]:
    units = [farm.get("farmer"), *(farm.get("hands") or [])]
    out: list[tuple[int, int]] = []
    for unit in units:
        if isinstance(unit, (list, tuple)) and len(unit) >= 2:
            out.append((int(unit[0]), int(unit[1])))
        else:
            out.append((0, 0))
    return out


def build_idle_rescue_agent(
    baseline: Baseline, allowed: frozenset[str] = ALLOWED_OPS
) -> Baseline:
    """Wrap a route so its refused actions become useful in-place work."""

    def decide(observation: dict[str, Any]) -> AgentAction:
        action = clone_action(baseline(observation))
        player = int(observation.get("player", 0))
        farms = observation.get("farms") or []
        if player >= len(farms) or not isinstance(farms[player], dict):
            return action
        farm = farms[player]
        tiles = farm.get("tiles") or []
        if not tiles:
            return action
        day = int(observation.get("day", 0))
        private = observation.get("private") or {}
        shed = {str(k): int(v) for k, v in (private.get("shed") or {}).items()}
        seeds = {str(k): int(v) for k, v in (private.get("seeds") or {}).items()}
        inventories = private.get("inventories") or []
        positions = _positions(farm)

        units = [action["farmer"], *action["hands"]]
        if len(units) != len(positions):
            return action
        for index, unit in enumerate(units):
            if not isinstance(unit, list) or not unit:
                continue
            x, y = positions[index]
            if not (0 <= y < len(tiles) and 0 <= x < len(tiles[y])):
                continue
            tile = tiles[y][x]
            known = (
                index < len(inventories)
                and isinstance(inventories[index], dict)
            )
            inventory = (
                {str(k): int(v) for k, v in inventories[index].items()}
                if known else {}
            )
            if not would_be_refused(
                unit, tile, inventory, seeds, shed, day, x, y,
                inventory_known=known,
            ):
                continue
            replacement = rescue_action(tile, inventory, day, allowed)
            if replacement is not None:
                units[index] = replacement
        action["farmer"] = units[0]
        action["hands"] = units[1:]
        return action

    return decide
