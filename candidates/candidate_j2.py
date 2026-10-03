"""Candidate J2 -- J, with ground treated as the scarce thing it is.

J is not short of seed, ground, labour or market allowance. Five separate
interventions proved that, each measured on sixty bracket tapes against
teams rated 2600-2900:

    crop cap doubled          12/120 wins   against 16/120 untouched
    fragile allowance x4,
      sale floor halved       16/120        no effect whatsoever
    planting cost halved      12/120
    cold-start radius         16/120        against 9/120 -- the one gain

And yet the bracket profile says J holds 45 plants at day 24 where those
teams hold 58, having decayed from 53, while a single-game trace catches
it sitting on six wheat and six tomato seed on day 21 with twelve tiles
bare. It has the seed. It has the ground. It does not sow.

WHY, AND WHAT THIS FILE CHANGES
===============================
J prices every job in coins per worker-turn and takes the best pairs
globally. That is the right idea and it is why J exists. But a turn is
not the only scarce resource on this board -- a TILE-DAY is, and the
auction cannot see it.

Consider a bare tile on day 15. Sowing it costs a turn now and books a
watering. Watering an existing crop returns coins sooner, so it wins the
auction, every turn, and the tile stays bare. Nothing in the rate ever
accounts for the fact that the bare tile earns nothing for the remaining
fourteen days while the watered one was going to be watered anyway. The
comparison is between a job and a job, never between a tile working and a
tile idle.

That is why every constant failed. PLANT_FUTURE_WEIGHT discounts what a
planting job is CHARGED; the crop cap changes how many tiles are ALLOWED.
Neither adds the missing term, which is what the ground gives up by
staying empty. So J2 adds it directly: a planting job's value carries the
tile-days it is about to fill, valued at what that crop earns per tile-day,
for as long as the season has left to run. Early, when a tile has twenty
days ahead of it, this is large and planting wins. Late, when a crop can
no longer mature, `crop_units` already returns zero and the term vanishes
with it, so the endgame is untouched.

Everything else is J. This module imports it, overrides one valuation, and
leaves the scheduler, the market layer, the plan and every constant alone.

    GROUND_VALUE = 0.0 is J exactly, and is the baseline this is measured
    against.
"""

from __future__ import annotations

from typing import Any

import candidates.candidate_j as J
from candidates.candidate_j import (CROPS, LAST_DAY, crop_turns, crop_units)

# Coins per tile-day that a bare tile is charged for staying bare, as a
# share of what the crop about to fill it actually earns per tile-day.
# One means the auction values the whole occupancy at face value; zero is
# J untouched.
GROUND_VALUE = 1.0
# Days of occupancy that may be counted. A crop cannot be credited for
# ground beyond the close, and the season is thirty days.
GROUND_HORIZON = float(LAST_DAY)


def ground_bonus(crop: str, day: int, revenue: float) -> float:
    """What filling this tile is worth beyond the first harvest.

    `revenue` is what the auction already credits: the batch this sowing
    will yield. The tile keeps working after that batch, and the crop's
    own cycle says for how long -- an ongoing crop delivers across its
    whole life, a short crop is resown. Both are ground held rather than
    ground idle, and neither is in the rate today.
    """
    if GROUND_VALUE <= 0.0 or revenue <= 0.0:
        return 0.0
    spec = CROPS.get(crop)
    if spec is None:
        return 0.0
    # Days this sowing occupies the tile before it is done with it.
    cycle = max(1.0, float(spec.get("first", 1)))
    # Days of season actually left for that occupancy to pay into.
    left = max(0.0, GROUND_HORIZON - float(day))
    if left <= 0.0:
        return 0.0
    # The batch already counted covers `cycle` days. Anything beyond that,
    # up to the close, is ground the auction is currently pricing at
    # nothing -- so credit it at the same rate the first batch earned.
    extra = max(0.0, min(left, GROUND_HORIZON) - cycle)
    if extra <= 0.0:
        return 0.0
    return GROUND_VALUE * (revenue / cycle) * extra


def _patch() -> None:
    """Wrap J's own job pricing so a sowing carries its occupancy."""
    original = J.job_offers

    def job_offers(ctx, plan, tile, x, y, inventory, day, step,
                   shed, seeds, counts):
        offers = original(ctx, plan, tile, x, y, inventory, day, step,
                          shed, seeds, counts)
        if GROUND_VALUE <= 0.0 or not offers:
            return offers
        out = []
        for coins, turns, action in offers:
            if (isinstance(action, (list, tuple)) and len(action) >= 2
                    and action[0] == "PLANT"):
                crop = action[1]
                # `crop_units` is zero for a crop that cannot reach its
                # first yield before the close, so a late sowing gets no
                # bonus and the endgame keeps J's own behaviour exactly.
                if crop_units(crop, day) > 0:
                    coins = coins + ground_bonus(crop, day, float(coins))
            out.append((coins, turns, action))
        return out

    J.job_offers = job_offers


_patch()


def agent(observation: dict[str, Any], configuration: Any = None):
    """Entry point. Must stay the last callable defined in this module."""
    return J.agent(observation, configuration)
