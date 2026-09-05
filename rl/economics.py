"""Marginal value of a farm action, in coins.

This is Agent E's core. Every constant here is transcribed from the
installed simulator (`kaggle_environments/envs/kaggriculture/`), not
guessed, and the pricing model is the simulator's own -- so an action's
score is an estimate of the coins it actually produces rather than a
hand-tuned priority number.

Why value rather than priority: sections 9j-9q measured that our market
policy and product mix are already fine (the reactive engine realises 88.5
coins per unit sold against a tape's 91.1) and that the entire gap is
throughput -- the engine spends 26% of worker-turns on tasks where a good
route spends 49%, burning the rest walking and idling. A scheduler that
ranks candidate actions by coins-per-turn attacks that directly: it cannot
idle while any positive-value task exists, and it prefers near work to far
work automatically because travel enters the denominator.

It also answers the question a fixed schedule cannot. A strawberry planted
too late to reach its yield window is worth nothing, so watering it is
worth nothing; the same tile replanted with wheat may still return several
cycles. Only a time-aware valuation can tell those apart, and this module
is where that judgement lives.
"""

from __future__ import annotations

from typing import Any


# --- simulator constants (kaggriculture.py) -------------------------------

# crop -> seed cost, first_yield_day, max_yield_day, interval, max_yield, ongoing
CROPS: dict[str, dict[str, Any]] = {
    "WHEAT": dict(seed=10, first=2, max_day=4, interval=0, max_yield=6, ongoing=False),
    "CARROT": dict(seed=20, first=2, max_day=3, interval=0, max_yield=4, ongoing=False),
    "TOMATO": dict(seed=50, first=8, max_day=8, interval=1, max_yield=4, ongoing=True),
    "STRAWBERRY": dict(seed=100, first=10, max_day=10, interval=2, max_yield=4, ongoing=True),
    "MELON": dict(seed=80, first=10, max_day=12, interval=0, max_yield=6, ongoing=False),
}
# animal -> cost, structure, first_yield_day, interval, max_held, product
ANIMALS: dict[str, dict[str, Any]] = {
    "GOOSE": dict(cost=300, structure="COOP", first=4, interval=1, max_held=4, product="EGG"),
    "COW": dict(cost=400, structure="PASTURE", first=8, interval=2, max_held=6, product="MILK"),
    "SHEEP": dict(cost=500, structure="PASTURE", first=6, interval=3, max_held=6, product="WOOL"),
}
BASE_PRICE: dict[str, int] = {
    "WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120,
    "MELON": 250, "EGG": 50, "MILK": 160, "WOOL": 200, "FERTILIZER": 100,
}
LAST_DAY = 29
TURNS_PER_DAY = 24


def days_left(day: int) -> int:
    """Whole production days remaining, including today."""
    return max(0, LAST_DAY - day)


def live_price(observation: dict[str, Any], item: str) -> float:
    """The market's current quote, falling back to base if unseen."""
    market = observation.get("market") or {}
    prices = market.get("prices") or {}
    value = prices.get(item)
    if isinstance(value, (int, float)) and value > 0:
        return float(value)
    return float(BASE_PRICE.get(item, 0))


def crop_can_mature(crop: str, planted_day: int, day: int) -> bool:
    """Will a tile planted on `planted_day` ever pay out before the end?

    This is the strawberry question: a crop whose first yield lands after
    the season ends is worth nothing at all, so no watering, fertilizing
    or harvesting effort spent on it can be justified.
    """
    spec = CROPS.get(crop)
    if spec is None:
        return False
    return planted_day + spec["first"] <= LAST_DAY


def remaining_waterings(crop: str, planted_day: int, day: int) -> int:
    """How many more yield-producing waterings this tile can still take.

    Non-ongoing crops only gain yield when watered inside
    [(max_day+1)//2, max_day] days of age; ongoing crops accrue on their
    own interval instead, so watering them protects the plant rather than
    adding units.
    """
    spec = CROPS.get(crop)
    if spec is None:
        return 0
    age = day - planted_day
    if spec["ongoing"]:
        return max(0, min(days_left(day), spec["max_yield"]))
    start = (spec["max_day"] + 1) // 2
    last = min(spec["max_day"], spec["max_day"] + days_left(day) - (age - age))
    if age > spec["max_day"]:
        return 0
    first_open = max(age, start)
    return max(0, min(last, LAST_DAY - day + age) - first_open + 1)


def water_value(
    observation: dict[str, Any],
    tile: dict[str, Any],
    day: int,
) -> float:
    """Coins gained by watering this tile now."""
    crop = str(tile.get("crop", ""))
    spec = CROPS.get(crop)
    if spec is None:
        return 0.0
    planted = int(tile.get("planted_day", day))
    if not crop_can_mature(crop, planted, day):
        return 0.0
    price = live_price(observation, crop)
    fertilized = int(tile.get("fertilized_until_day", -1)) >= day
    units = 2.0 if fertilized else 1.0
    if spec["ongoing"]:
        # Watering an ongoing crop does not itself add yield; it keeps the
        # plant alive so its own interval can. Value it as the yield at
        # risk if it dies, discounted by how close it is to dying.
        at_risk = int(tile.get("consecutive_unwatered", 0)) >= 1
        return price * units if at_risk else price * 0.25
    age = day - planted
    start = (spec["max_day"] + 1) // 2
    if age < start or age > spec["max_day"]:
        # Outside the window watering adds no yield; it only prevents the
        # weed death that follows two missed days.
        #
        # Pricing this rescue at the plant's *whole* remaining crop was
        # tried and collapsed the agent to zero reward: the rescue value
        # then dwarfed every harvest, so workers watered all game and never
        # banked anything. Job values in a greedy scheduler have to stay
        # commensurable, so this stays deliberately small.
        at_risk = int(tile.get("consecutive_unwatered", 0)) >= 1
        return price * 0.5 if at_risk else 0.0
    held = int(tile.get("yield_units", 0))
    if held >= spec["max_yield"]:
        return 0.0
    gained = min(units, spec["max_yield"] - held)
    return price * gained


def fertilize_value(
    observation: dict[str, Any],
    tile: dict[str, Any],
    day: int,
) -> float:
    """Coins gained by fertilizing, net of selling the fertilizer instead.

    Fertilizer doubles the yield each watering adds, for three days. Its
    worth is therefore the number of yield-adding waterings still available
    inside that window, times the crop price -- minus what the unit would
    have fetched on the market.
    """
    crop = str(tile.get("crop", ""))
    spec = CROPS.get(crop)
    if spec is None:
        return 0.0
    planted = int(tile.get("planted_day", day))
    if not crop_can_mature(crop, planted, day):
        return 0.0
    if int(tile.get("fertilized_until_day", -1)) >= day:
        return 0.0
    held = int(tile.get("yield_units", 0))
    headroom = max(0, spec["max_yield"] - held)
    if headroom <= 0:
        return 0.0
    age = day - planted
    if spec["ongoing"]:
        boosted = min(3, days_left(day), headroom)
    else:
        start = (spec["max_day"] + 1) // 2
        window_end = min(spec["max_day"], age + 2)
        boosted = max(0, window_end - max(age, start) + 1)
        boosted = min(boosted, headroom, days_left(day))
    if boosted <= 0:
        return 0.0
    gain = live_price(observation, crop) * boosted
    return gain - live_price(observation, "FERTILIZER")


def harvest_value(
    observation: dict[str, Any],
    tile: dict[str, Any],
) -> float:
    """Coins realisable from the units sitting on this tile."""
    units = int(tile.get("yield_units", 0))
    if units <= 0:
        return 0.0
    if "animal" in tile:
        product = ANIMALS[str(tile["animal"])]["product"]
        return live_price(observation, product) * units
    return live_price(observation, str(tile.get("crop", ""))) * units


def feed_value(
    observation: dict[str, Any],
    tile: dict[str, Any],
    day: int,
) -> float:
    """Coins protected by feeding this animal now.

    An animal unfed for two consecutive days escapes, forfeiting every
    remaining unit it would have produced, so feeding is worth the whole
    remaining production stream when it is about to bolt and much less
    otherwise.
    """
    animal = str(tile.get("animal", ""))
    spec = ANIMALS.get(animal)
    if spec is None or tile.get("fed_today"):
        return 0.0
    price = live_price(observation, spec["product"])
    remaining = days_left(day)
    if remaining <= 0:
        return 0.0
    future_units = remaining / max(1, spec["interval"])
    starving = int(tile.get("consecutive_unfed", 0)) >= 1
    stream = price * future_units
    return stream if starving else stream * 0.35


def care_value(
    observation: dict[str, Any],
    tile: dict[str, Any],
    day: int,
) -> float:
    """Care adds one bonus unit on the next fed production day."""
    animal = str(tile.get("animal", ""))
    spec = ANIMALS.get(animal)
    if spec is None or tile.get("cared_today"):
        return 0.0
    if days_left(day) <= 0:
        return 0.0
    if int(tile.get("yield_units", 0)) >= spec["max_held"]:
        return 0.0
    return live_price(observation, spec["product"])


def collect_fertilizer_value(observation: dict[str, Any], tile: dict[str, Any]) -> float:
    """A collected unit is worth whatever the best use of it is."""
    if not tile.get("fertilizer_available"):
        return 0.0
    return live_price(observation, "FERTILIZER")


def plant_value(observation: dict[str, Any], crop: str, day: int) -> float:
    """Expected coins from starting this crop now, net of the seed.

    Returns 0 for a crop that cannot reach its first yield before the
    season ends, which is what stops the agent sinking worker-turns into
    a strawberry that will never pay.
    """
    spec = CROPS.get(crop)
    if spec is None or not crop_can_mature(crop, day, day):
        return 0.0
    price = live_price(observation, crop)
    if spec["ongoing"]:
        productions = min(
            spec["max_yield"],
            max(0, (days_left(day) - spec["first"]) // max(1, spec["interval"]) + 1),
        )
        units = productions
    else:
        window = min(spec["max_day"], days_left(day))
        start = (spec["max_day"] + 1) // 2
        units = min(spec["max_yield"], max(0, window - start + 1))
    return price * units - spec["seed"]
