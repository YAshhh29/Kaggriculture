"""Sell at the rate the town actually absorbs, not as fast as we harvest.

This is the market demand engine applied where it turns out to matter --
not to what the farm *produces*, which section 10.8c measured as a dead
end, but to how fast it *sells*.

The mechanism is in the simulator's own step order:

    apply unit actions  ->  _process_market  ->  _town_consume

The town removes a fixed number of units of each product every four
steps -- one per unlocked shop that sells it, two for a single-product
shop, plus one of everything but fertilizer from the town centre every
twenty-four. Prices are a function of the shared market inventory, so
those removals are the only force pushing a price back up. Sell faster
than the town absorbs and inventory climbs, the price falls, and the farm
is competing against its own earlier sales for the rest of the game.

An elite route ignores this completely. It dumps 389 wool and realises 34
coins a unit; 347 milk at 92; 455 fertilizer at 36. Agent E, which sells
far less because it produces less, realises 170, 103 and 51 on the same
three products in the same games. The difference is not skill at pricing,
it is simply volume per unit of time.

So this paces sales against `candidates.demand.demand_rate` and holds the rest,
with four guards that override the pace, because a held unit is worthless
if any of them are true:

* the season is closing -- reward is the money on the books at step 720,
  so the last day sells everything;
* the shed is filling toward its 100-unit cap, past which the end-of-day
  drop discards the overflow;
* cash is short, since sales fund hiring, seed, feed and livestock;
* the product has no town demand at all (fertilizer), where holding only
  delays the inevitable.
"""

from __future__ import annotations

from typing import Any

from candidates.demand import demand_rate

LIVESTOCK = ("COW", "SHEEP", "GOOSE")
SHED_CAPACITY = 100
EPISODE_STEPS = 720
TURNS_PER_DAY = 24


def _shed(observation: dict[str, Any]) -> dict[str, int]:
    private = observation.get("private") or {}
    return {str(k): int(v) for k, v in (private.get("shed") or {}).items()}


def _money(observation: dict[str, Any]) -> float:
    player = int(observation.get("player", 0))
    farms = observation.get("farms") or []
    if player < len(farms) and isinstance(farms[player], dict):
        return float(farms[player].get("money", 0.0))
    return 0.0


def sell_allowance(
    observation: dict[str, Any],
    *,
    pace: float,
    cash_floor: float,
    shed_pressure: int,
    closing_day: int,
) -> dict[str, float] | None:
    """How many units of each product may be sold this turn.

    `None` means "no limit" -- one of the guards fired and everything
    should go. Otherwise the cap is the town's absorption over `pace`
    steps, so `pace` is the number of steps of demand a single turn's sale
    is allowed to consume.
    """
    step = int(observation.get("step", 0))
    day = step // TURNS_PER_DAY
    if day >= closing_day:
        return None
    if _money(observation) < cash_floor:
        return None
    if sum(_shed(observation).values()) >= shed_pressure:
        return None
    rate = demand_rate(observation)
    return {product: rate.get(product, 0.0) * pace for product in rate}


def paced_orders(
    observation: dict[str, Any],
    orders: list[list[Any]],
    *,
    pace: float = 24.0,
    cash_floor: float = 1200.0,
    shed_pressure: int = 80,
    closing_day: int = 29,
) -> list[list[Any]]:
    """Rewrite SELL orders so they never outrun the town's appetite.

    Everything that is not a SELL passes through untouched, and so does
    any product the town does not consume -- holding those only postpones
    the same price.
    """
    allowance = sell_allowance(
        observation,
        pace=pace,
        cash_floor=cash_floor,
        shed_pressure=shed_pressure,
        closing_day=closing_day,
    )
    if allowance is None:
        return orders
    out: list[list[Any]] = []
    for order in orders:
        if not (isinstance(order, list) and len(order) >= 3 and order[0] == "SELL"):
            out.append(order)
            continue
        item = str(order[1])
        if item in LIVESTOCK:
            out.append(order)
            continue
        cap = allowance.get(item, 0.0)
        if cap <= 0.0:
            # No town demand for this product at all; the price will never
            # recover, so there is nothing to wait for.
            out.append(order)
            continue
        quantity = min(int(order[2]), int(cap))
        if quantity > 0:
            out.append(["SELL", item, quantity])
    return out
