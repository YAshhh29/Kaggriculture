"""Candidate B: sequential-affordability market residual over Candidate A.

Hypothesis: in a real batch of market orders for one turn, Candidate A
sometimes places a SELL after a money- or shed-consuming order
(BUY_PRODUCT/BUY_SEED/BUY_ANIMAL/HIRE/BUY_LAND) that it funds. Because the
1.32.7 engine drains each order to completion before starting the next, a
sell positioned after a purchase cannot fund it -- moving eligible sells
earlier can only add cash/shed-room before later orders execute, never take
any away, so it can only keep every previously-successful order successful
and, sometimes, rescue one that used to fail.

Live replay of Candidate A's real 33-episode captured record found this
pattern almost entirely in WHEAT/FERTILIZER sells trailing an unrelated
spend (858 + 825 instances), not in premium sells (0 instances) -- so this
module moves any SELL, not just the four premium products the original
design brief singled out. That introduces a same-item overlap with
BUY_PRODUCT (which only ever targets WHEAT/FERTILIZER) that the premium-only
scope never had to consider: an exhaustive sweep over quantities and
inventory levels found no case where every order's fulfilled quantity tied
but final money still differed -- the engine's "quote a buy at post-buy
inventory" rule (built to make an unchanged-market buy/sell round-trip net
zero) appears to make same-item reordering money-neutral whenever nothing's
fulfillment changes, same as the cross-item case. That is an empirical
finding, not a proof, so `_is_strict_improvement` keeps a same-cost money
check as a free safety net rather than assuming the invariant is airtight.

This module only ever moves a SELL, never changes what the baseline chose
to buy -- but real replay still turned up a purchase type where *rescuing*
one is dangerous. Rescuing a HIRE is safe: Candidate A's own recovery
already re-aligns actions to the live hand count (extra/fewer hands is a
known, handled case). Rescuing a BUY_ANIMAL is not: the fixed calendar
never schedules care/feed for an animal it didn't plan for, and a rescued
animal can also fill the one pasture/coop slot the calendar's own later,
already-planned animal purchase needed. On real replay this cut both ways
in one batch of games: a rescued HIRE gained +8578 on episode 103977950,
while a rescued SHEEP purchase cost -37129 on episode 103937628 -- same
mechanism, opposite outcome, because only one of the two purchase types has
a downstream consumer of the state it creates. So `_is_rescue_barrier`
walls off BUY_ANIMAL specifically: a sell may still jump HIRE/BUY_PRODUCT/
BUY_SEED/BUY_LAND, but never crosses a BUY_ANIMAL order. BUY_SEED/BUY_LAND
are structurally closer to BUY_PRODUCT (inert until something later
chooses to use them, no ongoing care requirement, no capacity to block) but
have not been individually observed rescued in real replay either way.

A prior implementation of this module (order-safe premium re-*sorting* via
permutation search) was proven mathematically inert -- each product's price
depends only on that product's own running inventory, so permuting SELLs of
*already-fixed* quantities can never change total revenue -- and was
removed after live replay confirmed zero of 264 eligible firings ever
changed anything.

Second residual, added after two live episodes (105061000, 105062726) showed
the same calendar turn (record 200: [BUY_PRODUCT WHEAT 16, BUY_LAND]) spend
its way past the money a same-turn BUY_LAND needed, in both games, at both
seats. The calendar only ever attempts BUY_LAND twice in the whole 720-step
script (records 122 and 200); when the second attempt is starved this way it
is never retried, and every later scripted PLANT/WATER/HARVEST/BUILD_PASTURE
the calendar sends to that still-unowned quadrant reports the tile as the
literal string "LOCKED" and executes as a no-op for the rest of the episode
(471 such no-ops observed in each replay). `_land_priority_ordering` moves a
starved BUY_LAND ahead of any HIRE/BUY_PRODUCT/BUY_SEED/BUY_ANIMAL that
precedes it in the same turn, but never crosses a SELL in either direction
(a SELL only ever adds cash before land is evaluated, same reasoning as the
affordability pass, so its position is left to that pass entirely) and never
moves anything if BUY_LAND was not itself starved.

Unlike `_sequential_affordability_ordering`, this is not a strict-dominance
rule: displacing a HIRE/BUY_PRODUCT/BUY_SEED/BUY_ANIMAL order can and usually
does lower its fulfilled count, sometimes to zero. That is accepted on
purpose -- an entire quadrant (LAND_PRICES[1] = 2000, ~500 remaining steps of
extra planting/harvesting surface) is judged to dominate a partial WHEAT
restock or an extra hire on the turns actually observed -- rather than
proven via the same fulfilled-count invariant the sell pass relies on. The
one thing it does inherit from that pass's hard-won lesson: it only ever
reorders purchases against each other, never touches when a SELL reaches the
shared market, so it cannot reproduce the live-opponent price-timing risk
that walled off BUY_ANIMAL rescues and burned the BUY_SEED live gate above.
It has been checked against both failing replays and the full offline test
suite; it has not yet been run through a fresh live-opponent paired gate the
way the sell pass was, so treat it with the same "verify before fully
trusting at scale" posture that gate was built to enforce.

**`_land_priority_ordering` is DISABLED by default** (opt in with
`build_candidate_b_agent(enable_land_priority=True)`). The reason is risk,
not measured harm, and the distinction matters for anyone reading this later:

- Instrumented measurement over 8 complete games (5752 decisions, 3408
  non-empty market batches) found `_land_priority_ordering` changed the
  order 3 times and `_sequential_affordability_ordering` changed it 8
  times. The entire market layer alters roughly 1.4 decisions per game, so
  neither rule can account for a large live rating gap in either direction.
- The seeds 300-309 six-family gate scores 108-12 both with the rule
  (section 8's original A+B gate) and without it (the later no-land run),
  against the same 107-13 Candidate A control. That is a null result for
  this rule, not evidence against it.

So it is switched off because it is the one residual in this module that was
never justified by the fulfilled-count invariant -- it deliberately sacrifices
another purchase -- and a rule that fires ~0.4 times per game with no measured
benefit is not worth an unproven tail risk. Do not describe turning it off as
"fixing" a live regression: the measurements above cannot support that claim.
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

# (base, T, below_func, below_target, above_func, above_target) -- exact
# copy of the 1.32.7 simulator's MARKET_PARAMS for every sellable product,
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
