"""Candidate B: market-order reordering on top of Candidate A.

The engine fills each market order before starting the next, so a SELL queued
after a purchase cannot fund it. `_sequential_affordability_ordering` moves a
SELL ahead of a HIRE or BUY_PRODUCT, never another spend
(`_is_rescue_barrier`), and only when a local simulation shows no order fills
less; an exhaustive sweep found no money change when every fill ties.
`_land_priority_ordering` moves a cash-starved BUY_LAND ahead of other
same-turn purchases, giving up their fills for a whole quadrant. It is
DISABLED by default; enable it with
`build_candidate_b_agent(enable_land_priority=True)`.
"""

from __future__ import annotations

import math
from typing import Any

from agents.experimental_calendar_recovery_agent import agent as candidate_a
from rl.runtime import AgentAction, Baseline, clone_action


MAX_MARKET_ORDERS = 10
TERMINAL_MARKET_STEP = 717
MARKET_I0 = 10_000
PRICE_FLOOR = 1
HINGE_GAIN = 8.0

# (base, T, below_func, below_target, above_func, above_target) -- the
# 1.32.7 simulator's MARKET_PARAMS, exactly, for every sellable product,
# not just the four premium ones, because a faithful affordability check
# needs the real price of whatever else shares the same order batch.
MARKET_PARAMS = {
    "WHEAT": (25, 400, "sqrt", 0.80, "log", 0.20),
    "CARROT": (35, 450, "hinge", 1.00, "sqrt", 0.70),
    "TOMATO": (60, 200, "hinge", 0.40, "sqrt", 0.60),
    "STRAWBERRY": (120, 100, "sqrt", 0.70, "linear", 1.60),
    "MELON": (250, 300, "log", 0.20, "sq", 3.60),
    "EGG": (50, 332, "hinge", 0.40, "log", 0.20),
    "MILK": (160, 122, "sqrt", 0.60, "linear", 1.60),
    "WOOL": (200, 105, "log", 0.20, "sq", 3.20),
    "FERTILIZER": (100, 200, "linear", 0.40, "linear", 0.40),
}
SEED_COST = {
    "WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80,
}
ANIMAL_COST = {"GOOSE": 300, "COW": 400, "SHEEP": 500}
LAND_PRICES = (1000, 2000, 4000)
FARM_HAND_COST_MULT = 1
SHED_CAPACITY = 100


def _shape(function: str, value: float, scale: int) -> float:
    value = max(0.0, value)
    if function == "linear":
        return value
    if function == "sq":
        return value * value
    if function == "sqrt":
        return math.sqrt(value)
    if function == "log":
        return math.log(1.0 + value)
    if function == "hinge":
        if not scale or scale <= 0:
            return value
        unit = value / scale
        return unit + HINGE_GAIN * max(0.0, unit - 1.0) ** 2
    return value


def _market_price(product: str, inventory: int) -> int:
    base, scale, below_function, below_target, above_function, above_target = (
        MARKET_PARAMS[product]
    )
    if inventory < MARKET_I0:
        function = below_function
        target = below_target
        distance = MARKET_I0 - inventory
    else:
        function = above_function
        target = above_target
        distance = inventory - MARKET_I0
    amplitude = target * base / _shape(function, scale, scale)
    signed_change = (1 if inventory < MARKET_I0 else -1) * amplitude
    return max(
        PRICE_FLOOR,
        int(round(base + signed_change * _shape(function, distance, scale))),
    )


def _fib(n: int) -> int:
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def _hire_cost(hires_already_today: int) -> int:
    return FARM_HAND_COST_MULT * _fib(hires_already_today)


def _next_land_cost(unlocked_quadrant_count: int) -> int | None:
    extra = unlocked_quadrant_count - 1  # NW starts unlocked for free.
    if extra < 0 or extra >= len(LAND_PRICES):
        return None
    return LAND_PRICES[extra]


def _is_sell_order(order: list[Any]) -> bool:
    return (
        len(order) >= 3
        and str(order[0]) == "SELL"
        and int(order[2]) > 0
    )


_RESCUE_ELIGIBLE_OPS = {"HIRE", "BUY_PRODUCT"}


def _is_rescue_barrier(order: list[Any]) -> bool:
    """True for a spend a sell must never be moved across.

    Only HIRE and BUY_PRODUCT are trusted rescue targets; everything else
    (BUY_ANIMAL, BUY_SEED, BUY_LAND) is walled off. Captured-replay testing
    (no live opponent, opponent actions fixed regardless of our timing)
    made BUY_ANIMAL look uniquely dangerous: rescuing a SHEEP purchase cost
    -37129 relative to Candidate A on episode 103937628, because the fixed
    calendar never schedules care for an animal it didn't plan for and the
    rescue can fill the pasture/coop slot its own later purchase needed.
    But a live paired-game gate against a mirror-match opponent (which
    *does* react to shared market state, unlike a replay) showed the same
    "sell wheat before buying seed/hire" calendar turn cost -15302 and
    flipped a win to a loss via a BUY_SEED rescue alone, with BUY_ANIMAL
    already walled off -- proving the risk isn't animal-specific. It's
    shared-market timing: reordering our own trades shifts the price the
    opponent's own concurrent trades land on, an effect the isolated
    single-player safety simulation in `_simulate_orders` cannot see by
    construction. HIRE (Candidate A's own recovery already re-aligns to the
    live hand count) and BUY_PRODUCT have only shown benefit so far, in
    both replay and live-opponent testing (episode 103977950: +8578 replay;
    seed 305 vs distilled-calendar: improved margin live) -- but that is
    two spend types' worth of evidence, not proof the risk can never touch
    them too. Widen this set only against new, separately-gated evidence.
    """
    return len(order) >= 1 and str(order[0]) not in _RESCUE_ELIGIBLE_OPS \
        and str(order[0]) != "SELL"


def _has_reorder_opportunity(orders: list[list[Any]]) -> bool:
    """True if a sell sits after some other, non-barrier order."""
    seen_other = False
    for order in orders:
        if _is_rescue_barrier(order):
            seen_other = False
        elif _is_sell_order(order):
            if seen_other:
                return True
        else:
            seen_other = True
    return False


def _stable_partition_sells_first(
    tagged_orders: list[tuple[int, list[Any]]],
) -> list[tuple[int, list[Any]]]:
    """Sells-first within each run, never crossing a rescue barrier."""
    result: list[tuple[int, list[Any]]] = []
    run: list[tuple[int, list[Any]]] = []
    for item in tagged_orders:
        if _is_rescue_barrier(item[1]):
            sells = [entry for entry in run if _is_sell_order(entry[1])]
            rest = [entry for entry in run if not _is_sell_order(entry[1])]
            result.extend(sells)
            result.extend(rest)
            result.append(item)
            run = []
        else:
            run.append(item)
    sells = [entry for entry in run if _is_sell_order(entry[1])]
    rest = [entry for entry in run if not _is_sell_order(entry[1])]
    result.extend(sells)
    result.extend(rest)
    return result


def _simulate_orders(
    *,
    money: float,
    shed: dict[str, int],
    market_inventory: dict[str, int],
    hires_today: int,
    unlocked_quadrant_count: int,
    tagged_orders: list[tuple[int, list[Any]]],
) -> tuple[float, dict[int, int]]:
    """Replay one player's own order queue in isolation.

    Mirrors the 1.32.7 engine's per-order-then-per-unit commit loop for a
    single player's queue. Ignores simultaneous opponent trading on the same
    product at the same queue position -- an approximation already relied on
    elsewhere in this module for premium pricing -- but since both the
    baseline and candidate orderings are replayed under the identical
    approximation, the comparison between them stays valid.
    """
    shed = dict(shed)
    market_inventory = dict(market_inventory)
    fulfilled: dict[int, int] = {}
    for tag, order in tagged_orders:
        fulfilled[tag] = 0
        if not order:
            continue
        op = str(order[0])
        if op in ("SELL", "BUY_PRODUCT", "BUY_SEED", "BUY_ANIMAL"):
            if len(order) < 3:
                continue
            item = str(order[1])
            try:
                requested = int(order[2])
            except (TypeError, ValueError):
                continue
            if requested <= 0:
                continue
            if op == "SELL":
                if item not in market_inventory:
                    continue
                for _ in range(requested):
                    if shed.get(item, 0) <= 0:
                        break
                    price = _market_price(item, market_inventory[item])
                    shed[item] -= 1
                    money += price
                    if price > 1:
                        market_inventory[item] += 1
                    fulfilled[tag] += 1
            elif op == "BUY_PRODUCT":
                if (
                    item not in ("WHEAT", "FERTILIZER")
                    or item not in market_inventory
                ):
                    continue
                for _ in range(requested):
                    price = _market_price(item, market_inventory[item] - 1)
                    if money < price or sum(shed.values()) >= SHED_CAPACITY:
                        break
                    money -= price
                    shed[item] = shed.get(item, 0) + 1
                    market_inventory[item] -= 1
                    fulfilled[tag] += 1
            elif op == "BUY_SEED":
                if item not in SEED_COST:
                    continue
                price = SEED_COST[item]
                for _ in range(requested):
                    if money < price:
                        break
                    money -= price
                    fulfilled[tag] += 1
            elif op == "BUY_ANIMAL":
                if item not in ANIMAL_COST:
                    continue
                price = ANIMAL_COST[item]
                for _ in range(requested):
                    if money < price or sum(shed.values()) >= SHED_CAPACITY:
                        break
                    money -= price
                    shed[item] = shed.get(item, 0) + 1
                    fulfilled[tag] += 1
        elif op == "HIRE":
            cost = _hire_cost(hires_today)
            if money >= cost:
                money -= cost
                hires_today += 1
                fulfilled[tag] = 1
        elif op == "BUY_LAND":
            cost = _next_land_cost(unlocked_quadrant_count)
            if cost is not None and money >= cost:
                money -= cost
                unlocked_quadrant_count += 1
                fulfilled[tag] = 1
        # Any other/malformed op is left at fulfilled[tag] = 0, matching the
        # simulator's "malformed sub-op aborts this order" behavior.
    return money, fulfilled


def _is_strict_improvement(
    baseline: tuple[float, dict[int, int]],
    candidate: tuple[float, dict[int, int]],
) -> bool:
    """True if no order lost fulfillment, and something measurably improved.

    Never reject on final money alone: a rescued purchase spends money that
    a failed purchase would have left idle, so a rescued order's fulfilled
    count rising is itself the win, regardless of leftover cash. When every
    fulfilled count ties instead, fall back to requiring strictly more
    money -- not because a same-item sell/BUY_PRODUCT overlap is known to
    produce a money difference on a fulfilled tie (see module docstring: an
    exhaustive sweep found none), but because there is no proof it never
    can, and this check is free insurance if it ever does.
    """
    baseline_money, baseline_fulfilled = baseline
    candidate_money, candidate_fulfilled = candidate
    if any(
        candidate_fulfilled[tag] < count
        for tag, count in baseline_fulfilled.items()
    ):
        return False
    if any(
        candidate_fulfilled[tag] > count
        for tag, count in baseline_fulfilled.items()
    ):
        return True
    return candidate_money > baseline_money


def _sequential_affordability_ordering(
    observation: dict[str, Any],
    market_orders: list[list[Any]],
) -> list[list[Any]]:
    """Move sells ahead of spends they could otherwise fund.

    Never invents, drops, or resizes an order -- only reorders the exact
    batch the baseline already chose -- and only takes effect when a local
    replay proves the reordered batch strictly dominates the baseline batch
    (never a smaller fulfilled quantity on any order, never less cash when
    every order's fulfilled quantity ties).
    """
    if int(observation.get("step", 0)) >= TERMINAL_MARKET_STEP:
        return market_orders
    if not market_orders or len(market_orders) > MAX_MARKET_ORDERS:
        return market_orders
    if not _has_reorder_opportunity(market_orders):
        return market_orders

    tagged = list(enumerate(market_orders))
    candidate_tagged = _stable_partition_sells_first(tagged)
    candidate_orders = [order for _, order in candidate_tagged]
    if candidate_orders == market_orders:
        return market_orders

    market = observation.get("market", {})
    market_inventory = {
        str(item): int(quantity)
        for item, quantity in market.get("inventory", {}).items()
    }
    if not market_inventory:
        return market_orders
    private = observation.get("private", {})
    shed = {
        str(item): int(quantity)
        for item, quantity in private.get("shed", {}).items()
    }
    player = int(observation.get("player", 0))
    farms = observation.get("farms")
    if not farms or player >= len(farms):
        return market_orders
    farm = farms[player]
    money = float(farm.get("money", 0))
    hires_today = int(farm.get("hires_today", 0))
    unlocked_quadrant_count = len(farm.get("unlocked_quadrants", []))

    baseline_outcome = _simulate_orders(
        money=money,
        shed=shed,
        market_inventory=market_inventory,
        hires_today=hires_today,
        unlocked_quadrant_count=unlocked_quadrant_count,
        tagged_orders=tagged,
    )
    candidate_outcome = _simulate_orders(
        money=money,
        shed=shed,
        market_inventory=market_inventory,
        hires_today=hires_today,
        unlocked_quadrant_count=unlocked_quadrant_count,
        tagged_orders=candidate_tagged,
    )
    if _is_strict_improvement(baseline_outcome, candidate_outcome):
        return candidate_orders
    return market_orders


_LAND_PRIORITY_DISPLACERS = {"BUY_PRODUCT", "BUY_SEED", "HIRE", "BUY_ANIMAL"}


def _is_land_order(order: list[Any]) -> bool:
    return len(order) >= 1 and str(order[0]) == "BUY_LAND"


def _land_first_ordering(
    tagged_orders: list[tuple[int, list[Any]]],
) -> list[tuple[int, list[Any]]]:
    """Walk each BUY_LAND order back past adjacent non-SELL spends.

    Stops the moment it hits a SELL, another BUY_LAND, or the start of the
    batch -- so this never changes a SELL's position (that stays entirely
    the affordability pass's decision) and never reorders two BUY_LAND
    orders relative to each other.
    """
    result = list(tagged_orders)
    for index in range(len(result)):
        if not _is_land_order(result[index][1]):
            continue
        insert_at = index
        while insert_at > 0 and str(result[insert_at - 1][1][0]) \
                in _LAND_PRIORITY_DISPLACERS:
            insert_at -= 1
        if insert_at != index:
            item = result.pop(index)
            result.insert(insert_at, item)
    return result


def _land_priority_ordering(
    observation: dict[str, Any],
    market_orders: list[list[Any]],
) -> list[list[Any]]:
    """Rescue a BUY_LAND a preceding same-turn spend would otherwise starve.

    Only fires when reordering flips at least one BUY_LAND order from
    failing (fulfilled 0) to succeeding (fulfilled 1) in local simulation;
    see the module docstring for why this trades a purchase's fulfilled
    count away on purpose rather than requiring it never drop.
    """
    if int(observation.get("step", 0)) >= TERMINAL_MARKET_STEP:
        return market_orders
    if not market_orders or len(market_orders) > MAX_MARKET_ORDERS:
        return market_orders
    if not any(_is_land_order(order) for order in market_orders):
        return market_orders

    tagged = list(enumerate(market_orders))
    candidate_tagged = _land_first_ordering(tagged)
    candidate_orders = [order for _, order in candidate_tagged]
    if candidate_orders == market_orders:
        return market_orders

    market = observation.get("market", {})
    market_inventory = {
        str(item): int(quantity)
        for item, quantity in market.get("inventory", {}).items()
    }
    if not market_inventory:
        return market_orders
    private = observation.get("private", {})
    shed = {
        str(item): int(quantity)
        for item, quantity in private.get("shed", {}).items()
    }
    player = int(observation.get("player", 0))
    farms = observation.get("farms")
    if not farms or player >= len(farms):
        return market_orders
    farm = farms[player]
    money = float(farm.get("money", 0))
    hires_today = int(farm.get("hires_today", 0))
    unlocked_quadrant_count = len(farm.get("unlocked_quadrants", []))

    baseline_outcome = _simulate_orders(
        money=money,
        shed=shed,
        market_inventory=market_inventory,
        hires_today=hires_today,
        unlocked_quadrant_count=unlocked_quadrant_count,
        tagged_orders=tagged,
    )
    candidate_outcome = _simulate_orders(
        money=money,
        shed=shed,
        market_inventory=market_inventory,
        hires_today=hires_today,
        unlocked_quadrant_count=unlocked_quadrant_count,
        tagged_orders=candidate_tagged,
    )
    land_tags = [tag for tag, order in tagged if _is_land_order(order)]
    baseline_fulfilled = baseline_outcome[1]
    candidate_fulfilled = candidate_outcome[1]
    rescued = any(
        baseline_fulfilled.get(tag, 0) == 0
        and candidate_fulfilled.get(tag, 0) == 1
        for tag in land_tags
    )
    return candidate_orders if rescued else market_orders


def build_candidate_b_agent(
    *,
    baseline: Baseline = candidate_a,
    enable_land_priority: bool = False,
) -> Baseline:
    """Create Candidate A plus the market-timing residuals."""
    def decide(observation: dict[str, Any]) -> AgentAction:
        action = clone_action(baseline(observation))
        market = _sequential_affordability_ordering(
            observation,
            action["market"],
        )
        action["market"] = (
            _land_priority_ordering(observation, market)
            if enable_land_priority
            else market
        )
        return action

    return decide


agent = build_candidate_b_agent()
