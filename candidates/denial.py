"""Price a sale by what it costs the opponent, not only by what it pays us.

This exists because of one measurement (GOAL.md 10.8t). The same frozen
opponent tape, the same seed, only our side changed:

    against Candidate D   the opponent banks   59,943
    against Agent E       the opponent banks  142,772

The opponent's actions are a recording and its farm is its own. The single
thing our play changes is **the price it sells at**, because price is a
function of one market inventory both players share. D dumps about 2,140
units a game and the price collapses under the opponent; E sells 977,
realises a far better price per unit, and leaves the market standing for
the opponent to harvest. E earns the most coins of any agent in this
project and won 0 of 64 held-out games.

Every value in `rl/economics` prices a job by the coins *we* gain. On a
shared market half the result is the coins the opponent does not gain, and
nothing in E can see that term. This module is that term.

**The rival's farm is public.** `observation["farms"][1 - player]` carries
their tiles, so their crops, their animals and the yield already standing
on each are all readable. That is enough to estimate what they still have
to sell, and therefore how much a sale of ours costs them.

Note the asymmetry that makes this worth doing at all: selling a unit into
a floored price earns us almost nothing, so `candidates/sell_floor.py` held it
back -- and holding it back was measured to be how an agent hands its
opponent the game. A unit that earns us 3 coins and costs the opponent 40
is a good unit to sell. Nothing in the codebase could express that before.
"""

from __future__ import annotations

from typing import Any

from candidates.demand import ANIMAL_PRODUCT
from candidates.economics import ANIMALS, CROPS, LAST_DAY, days_left
from candidates.market import inventory_of, price_at

TURNS_PER_DAY = 24


def _rival(observation: dict[str, Any]) -> dict[str, Any]:
    player = int(observation.get("player", 0))
    farms = observation.get("farms") or []
    other = 1 - player
    if 0 <= other < len(farms) and isinstance(farms[other], dict):
        return farms[other]
    return {}


def rival_supply(observation: dict[str, Any], item: str) -> float:
    """Units of `item` the rival's visible farm can still bring to market.

    Counts what is already standing as yield plus what its animals and
    ongoing crops will still produce before the season ends. Deliberately
    an estimate: it cannot see their shed, and a crop's future yield
    depends on whether they keep watering it. Both errors are downward,
    which is the safe direction -- underestimating the rival's supply
    understates the value of denying it, so this never talks the agent
    into a sale on an imagined threat.
    """
    day = int(observation.get("day", 0))
    left = max(0, days_left(day))
    if left <= 0:
        return 0.0

    total = 0.0
    for row in (_rival(observation).get("tiles") or []):
        for tile in row:
            if not isinstance(tile, dict):
                continue
            standing = float(tile.get("yield_units", 0) or 0)
            if "animal" in tile:
                animal = str(tile["animal"])
                if ANIMAL_PRODUCT.get(animal) != item:
                    continue
                spec = ANIMALS.get(animal)
                if spec is None:
                    continue
                interval = max(1, int(spec["interval"]))
                total += standing + left / interval
            elif tile.get("kind") == "PLANT":
                if str(tile.get("crop", "")) != item:
                    continue
                spec = CROPS.get(item)
                total += standing
                if spec is not None and spec.get("ongoing"):
                    interval = max(1, int(spec["interval"]))
                    held = int(tile.get("yield_units", 0) or 0)
                    room = max(0, int(spec["max_yield"]) - held)
                    total += min(room, left / interval)
    return total


def denial_value(
    observation: dict[str, Any],
    item: str,
    units: float,
    *,
    share: float = 1.0,
) -> float:
    """Coins the rival loses because our `units` moved the price first.

    Their supply is sold into a market our sale has already pushed up, so
    they walk down a lower stretch of the same curve. The difference
    between the two stretches is what the sale denied them.

    `share` discounts the estimate for everything this cannot know -- when
    in the day they sell, what the town lifts back out in between, whether
    they harvest at all. It is a parameter because the right value is a
    measurement, not a derivation.
    """
    units = int(max(0.0, units))
    supply = int(max(0.0, rival_supply(observation, item)))
    if units <= 0 or supply <= 0 or share <= 0.0:
        return 0.0
    start = inventory_of(observation, item)
    without = sum(price_at(item, start + n) for n in range(supply))
    withus = sum(price_at(item, start + units + n) for n in range(supply))
    return max(0.0, (without - withus) * share)


def contested_value(
    observation: dict[str, Any],
    item: str,
    units: float,
    *,
    share: float = 1.0,
) -> float:
    """What a sale is worth once the opponent's loss is counted too.

    This is the number a two-player market decision should use, and the
    one `rl/economics` has never had.
    """
    from candidates.market import sale_revenue

    return (
        sale_revenue(observation, item, units)
        + denial_value(observation, item, units, share=share)
    )


def contested_items(
    observation: dict[str, Any],
    *,
    minimum: float = 1.0,
) -> dict[str, float]:
    """Every good the rival can still supply, and how much of it.

    A sale into one of these is worth more than its own revenue; a sale
    into anything else is worth exactly its revenue and nothing more.
    """
    out: dict[str, float] = {}
    for item in (*CROPS, *ANIMAL_PRODUCT.values()):
        supply = rival_supply(observation, item)
        if supply >= minimum:
            out[item] = supply
    return out
