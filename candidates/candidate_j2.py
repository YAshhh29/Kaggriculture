"""Candidate J2: Candidate J with the cost of idle ground added to planting.

J's auction compares job against job and never charges a bare tile for staying
bare, so watering keeps outbidding sowing and ground sits idle mid-season (J
holds 45 plants on day 24 where 2600-2900 rated teams hold 58). J2 wraps J's
`job_offers` and credits each PLANT offer with the tile-days the crop will
occupy beyond its first batch, up to the close, at the rate that batch earns.
Sowings too late to mature get no credit, so J's endgame is unchanged, and
everything else is J's.

GROUND_VALUE = 0.0 reproduces J exactly and is the baseline.
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
