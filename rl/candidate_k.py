"""Candidate K: H2's farm, sold at J's prices.

The two agents this project has are each missing exactly what the other has.

H2 grows. It works 58.0 of its 60.3 tiles where J works 50.7 of 61, stands
18.7 strawberry to J's 10.5 and 6.1 cows to J's 3.5, puts 65,630 coins a
game of inputs through the market to J's 17,620, and turns over 181,907 of
goods to J's 115,336. On the honest breadth panel it wins 27 of 48 clean
games where J wins 5 of 47, and head to head it beats J by 67,202 a game.

And then it gives the crop away. Its own audit, per game:

    strawberry   249 units at 109.6 coins, 9% BELOW base, 92 of them
                 under a quarter of base
    wool         169 units at 167.0, 16% below base, 38 under a quarter
    milk         190 units at 131.1, 18% below base, 76 under a quarter

J sells those same goods at 189.7, 227.5 and 96.6 -- strawberry 58% ABOVE
base, wool 14% above -- because it meters each book against its own depth.
The books are shallow beyond belief: wool gives up a quarter of its price
over 51 units and strawberry over 48, while wheat takes two thousand. H2
sells whatever its route projects, in one lot, into a book sixteen units
deep.

Strawberry alone is 249 units at 80 coins of difference. So K was built as
H2 unaltered, with one thing added: before the action leaves, every sale of
a fragile good is cut back to what the book will pay for. The route, the
timing layers and the opening are untouched.

**WHAT K ACTUALLY IS TODAY, 2026-09-23.** That added thing is currently
switched off and this docstring described an agent that no longer exists.
Walk `meter()` with the constants as they stand -- FLOOR 0.0, LOT 0,
WHEAT_BUY_CAP 0, FERTILIZER_BUY True -- and every branch falls through to
`out.append(list(order))`. It rebuilds the order list identically. Both
the lot cap and the price floor were measured and turned off in earlier
sessions, for reasons recorded on each constant, and nothing was left
behind. So K is H2's route plus `extend()`'s extra hires, and the sale
metering in the title is dead code until LOT or FLOOR is set.

That matters because the defect it was built for is still happening.
Profiling sixteen games against teams rated 2600-2900
(tools.analysis.bracket_profile): they issue ZERO dump-all orders a game,
K issues 77, starting around step 671. When they name a quantity we match
them exactly -- median lot 4 against 4, p90 13 against 12 -- so the whole
difference is the endgame, where H2's route sells each good in one
"SELL <GOOD> 1000" that walks the glut curve down unit by unit.

Two rules from J's measurements come with it, both learned expensively:

* The meter lifts when the shed is tight. Holding stock to protect a price
  loses -- the hundred-slot shed is what binds late, and a freed slot is
  worth more than the coins the freeing unit gives up. Measured twice in J,
  at 78,490 and 80,385 against 80,730.
* Wheat, egg and carrot are never metered. Their books are bottomless, the
  town eats some nine hundred wheat a game, and J sells every unit of those
  three above base already.
"""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from typing import Any

from rl.economics import BASE_PRICE
import rl.candidate_j as _reactive
from rl.crew_extra import actions_for
from rl.market import MARKET_PARAMS, inventory_of, price_at

_PATH = (Path(__file__).resolve().parents[1] / "submissions"
         / "candidate-h2" / "main.py")
_spec = importlib.util.spec_from_file_location("candidate_k_h2_core", _PATH)
_core = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_core)

# The books worth protecting, and the share of base below which a sale is not
# worth making on an ordinary turn. Fertilizer is deliberately absent: it is
# the one good the town never eats, so holding it only costs a shed slot, and
# metering it was measured in J and lost.
FRAGILE = ("WOOL", "STRAWBERRY", "MILK", "MELON")
# A price floor is the wrong instrument and it was measured as such: every
# degree of it costs money, monotonically, 82,928 at 0.55 and 85,854 at 0.30
# against 96,082 with none. It has a trap, too -- once a book is already
# below the floor the computed allowance is zero and the good is never sold
# again, so stock piles up and the hundred-slot shed jams.
FLOOR = 0.0
# The right instrument is the LOT. An independent study of the top-200
# corpus finds the teams rated 3000+ sell premium goods in lots averaging
# 3.7 units (p90 six) where the 2800 band sells 7.8 (p90 twelve), and take
# the same money from 87 units of wool that the field takes from 110. The
# glut curves are why: wool gives up a quarter of its price over 51 units
# and strawberry over 48. A lot cap always sells something, so the cash
# cycle that funds H2's 65,630 a game of inputs keeps turning -- which is
# precisely what the floor broke.
# Measured and off. The lot cap holds our own price -- median 95,178 at
# four against H2's 96,082 -- and hands the game away: the opponent's median
# rises from 92,587 to 106,559 and our clean wins fall from 27 of 48 to 4 of
# 50. `_process_market` walks both players' orders by index against the same
# pre-commit inventory, so selling early and heavily is not impatience, it
# is denial: it crashes the shared book before their orders land. Metering
# stops us denying them. Every price experiment in this project lost for
# this reason, and it took measuring the OPPONENT's column to see it.
LOT = 0

# What H2 overdoes, from an independent study of the top-200 corpus. Per
# game the teams rated 3000+ buy 183 units of market wheat and the 2800
# band buys 313; H2 buys 1,165. The same study finds the field dumps
# fertilizer at 45 a unit and then buys 91 of it back -- H2 buys back 231 --
# into the one good the town never eats, whose inventory therefore only ever
# rises. Nought disables each cap.
# Measured and off. On thirty teams a cap of six looked worth 1,832 a game
# on the median; on forty it is noise and the truth is monotonic the other
# way -- 89,098 at a cap of three, 93,944 at ten, 96,082 with none. Buying
# is denial as much as selling is: BUY_PRODUCT takes stock out of the
# market, and the study's ELITE buy 183 units of wheat a game to H2's 1,165
# in games where nobody is racing them for it.
WHEAT_BUY_CAP = 0

# --- the crew the route never planned for -----------------------------
#
# This is the one lever a recorded route structurally cannot reach, and the
# study of the top-200 corpus calls it the clearest unexploited edge in the
# dataset: both cohorts stop at eleven hands while holding 7,600+ coins and
# leaving 22 tiles bare on day 28. Hiring is a fibonacci curve on the count
# already taken today and it resets each night, so the n-th hand costs
# fib(n) outright -- 144 for the twelfth, 233 for the thirteenth, 377 for
# the fourteenth -- against a job-turn measured at 37.3 coins.
#
# The route has no action to give those hands, so rl/crew_extra.py does:
# take the job under your feet, else step toward the nearest one worth the
# walk, else stand. It only has to beat standing still.
# Measured and off: the lever is already taken. H2 ends a game with
# THIRTEEN hands where the corpus caps at eleven, so the study's unhired
# twelfth does not exist here, and pushing past thirteen collapses exactly
# as it does everywhere else on this board -- 146,301 at one extra hand and
# 34,925 at three, against 167,832 at none. The crew is rented again every
# night on a fibonacci curve and a hand too many is ruinous.
EXTRA_HANDS = 0
# What is NOT taken is the standing still. H2 passes 7.2% of its
# worker-turns, the same share as the 2800 band, and those are hands it has
# already paid for. A pass is worth nothing; the worst job on the board is
# worth more. So a hand the route leaves idle is given the job under its
# feet, or a step toward the nearest one worth the walk.
# Measured, off, and the most instructive failure of the lot: 90,409
# against 184,922. Overriding a PASS MOVES a hand, and H2's route is a
# recorded programme that assumes where every hand is standing -- relocate
# one and every scripted action it is given afterwards lands on the wrong
# tile. That is why nothing bolted onto this agent has ever helped: it is a
# frozen programme, and any deviation desyncs the rest of it. The way past
# H2 is not to modify H2.
FILL_IDLE = False
# Cash that must remain after the hire, so the spare crew never starves the
# route's own buying -- which is what funds the farm it is working.
HIRE_RESERVE = 2500.0
# Hire only while a hand still has most of a day to work.
HIRE_BEFORE_HOUR = 3

# --- the splice ---------------------------------------------------------
#
# The study of the corpus found what separates the top of the ladder from
# the 2800 band, and it is not the farm: production is at parity, 1,769
# units a game either way. It is that the leaders RE-DECIDE. Comparing each
# team's farmer action across its own games, the 2800 band repeats 95.7% of
# them and first diverges at step 258; the teams rated 3000+ repeat 40.5%
# and diverge at step 40. Rank 1 is byte-identical for steps 0-11, identical
# again 14-25, and completely different in every game from step 26.
#
# What they keep is the opening. So this was tried: H2's recorded route
# plays the first SPLICE steps -- an opening that reaches 58 worked tiles
# of 60 and wastes nothing -- and the reactive engine takes the farm on
# from there. Nought hands the whole game to H2 and is the agent we
# already had, with only the fragile-goods meter added.
#
# It was also the cleanest diagnostic available: if splicing early scores
# like J, J's weakness is its midgame; if late, its opening. Day nine
# scored 81,122 and day twelve 86,028 against the route alone at 96,082,
# so the trend said later is better, and that was the diagnostic
# answering itself: the reactive engine was weaker than the route at
# every stage, not just the opening. Kept anyway at the time, on a
# robustness argument: an agent that re-decides can answer an opponent a
# recorded route cannot, and that is what the corpus says separates 3000
# from 2800.
#
# Re-measured 2026-09-23 against strong_panel after J's cold-start fix
# (COLD_START_RADIUS, candidate_j.py) -- the fix that should have helped
# the reactive engine most, since it is exactly the kind of midgame
# defect the diagnostic above was built to find. It did not close the
# gap; splice=0 still wins on every single opponent, by more than before
# in absolute terms:
#     aurax7  splice=0 -990      splice=216 -48,114   splice=288 -31,662
#     v34     splice=0 +54,689   splice=216 +13,117   splice=288 +15,905
#     h2      splice=0 +0        splice=216 -30,935   splice=288 -31,202
#     i       splice=0 +4,437    splice=216 -35,362   splice=288 -26,873
# The robustness argument for keeping a splice is untested, not
# disproven -- strong_panel's opponents are strong but none of them are
# built to specifically exploit a scripted, predictable route, so this
# does not settle whether a splice would earn its keep against one that
# is. It does settle which config is better against everything actually
# measured, which is what the ladder is made of until shown otherwise.
SPLICE = 0
# Measured and left alone. The study is right that the field dumps
# fertilizer and buys it back into a book the town never drains, but
# stopping H2 doing it costs 1,116 a game on the median: it needs the
# manure on its own crops more than it needs the coins back.
FERTILIZER_BUY = True
SHED_CAP = 100

# --- the endgame, which is the one thing the bracket actually does
# --- differently ---------------------------------------------------------
#
# Profiling sixteen games against teams rated 2600-2900
# (tools.analysis.bracket_profile) found production at parity -- their crew,
# plants and herd track ours day for day, and we finish day 29 slightly
# ahead on money -- and exactly one behavioural gap. They issue ZERO
# dump-all orders a game. We issue 77, every one of them from about step
# 671, because H2's route liquidates each good in a single
# "SELL <GOOD> 1000". The engine fills that unit by unit down the glut
# curve (`_commit_unit`), so a shallow book pays less for every unit after
# the first: wool gives up a quarter of its price over 51 units and
# strawberry over 48. On sized orders we are indistinguishable from them,
# median lot 4 against 4 and p90 13 against 12.
#
# `meter` was built for exactly this and cannot do it, for two reasons that
# are both fixed here rather than tuned around:
#   1. it lifts entirely when the shed is tight, and in the endgame the
#      shed is ALWAYS tight, so it is off precisely when it is needed;
#   2. FLOOR was measured and abandoned because once a book is already
#      under the floor the allowance computes to zero, the good is never
#      sold again, stock piles up and the hundred-slot shed jams.
# So the floor here is never allowed to return zero: SPREAD_MIN units
# always go, which drains the book steadily instead of seizing.
#
# Steps before the last acting step over which the shed is emptied
# gradually rather than dumped.
#
# MEASURED AND BACKWARDS. Built on the dump-order count above and it was
# the wrong reading of it: order SHAPE is not sale TIMING. Tracking the
# shed itself over eight bracket games settles what they actually do --
# they are not spreading a dump, they never build the pile:
#       day      22    24    26    28
#       THEM      6     2     2     6   units held
#       US       40    23    38    28
# They run the shed near empty from day 22 on. We carry 20-40 units late
# and then liquidate. Spreading that liquidation makes K hold LONGER,
# which is the opposite of the gap, and it measures that way: 92,446 at
# off against 92,251 at 48 steps and 89,869 at 96. Left at zero, and the
# real mechanism is DRAIN_TO below, which sells sooner instead.
ENDGAME_SPREAD = 0
# Share of base the book must still pay for a unit to be worth selling now
# rather than a few turns later, once the town has eaten some of it.
SPREAD_FLOOR = 0.45
# Units always permitted even when the book is already under the floor.
# This is the anti-jam rule; without it this mechanism is the old FLOOR.
SPREAD_MIN = 3
LAST_ACT_STEP = 718

# Units the shed may hold before spare market slots are spent selling it
# down. Zero disables and is H2's own behaviour.
#
# This is the same evidence as ENDGAME_SPREAD read the right way round.
# The bracket holds 2-6 units from day 22; the route holds 20-40. Stock in
# the shed is not money -- the score is coins held -- and it is not safety
# either, because price depends on inventory alone and there is no recovery
# with time, only the town eating. Holding a unit therefore gains nothing
# and risks the hundred-slot shed jamming against the harvest. Selling it
# sooner also crashes the shared book before the opponent's orders land,
# which is the denial that every price experiment in this project
# eventually ran into from the wrong side.
#
# Only SPARE slots are used. The engine reads ten orders a turn and the
# route's own come first; appending cannot shift them, but anything past
# the tenth is dropped, so this never displaces a route order.
DRAIN_TO = 0
# Never push a unit below this share of base while draining -- a drain is
# not a reason to give the crop away.
DRAIN_FLOOR = 0.55

# Above this the shed is the binding constraint and the meter comes off.
CRAMPED = SHED_CAP - 12


for _key, _value in json.loads(os.environ.get("K_SET", "{}")).items():
    globals()[_key] = _value


def _shed_total(observation: dict[str, Any]) -> int:
    private = observation.get("private") or {}
    shed = private.get("shed") or {}
    try:
        return sum(int(v) for v in shed.values())
    except (TypeError, ValueError):
        return 0


def meter(observation: dict[str, Any], market: list) -> list:
    """Cut each fragile sale back to what its book will actually pay for.

    Price is a function of inventory alone -- there is no recovery with time
    -- so a unit sold raises the inventory permanently and only the town
    eating brings it down again. Selling past the floor is not impatience,
    it is handing over the rest of the game's production at a lower price.
    """
    if not market:
        return market
    tight = _shed_total(observation) >= CRAMPED
    step = int(observation.get("step", 0) or 0)
    endgame = bool(ENDGAME_SPREAD) and step >= LAST_ACT_STEP - ENDGAME_SPREAD
    out = []
    for order in market:
        if (isinstance(order, (list, tuple)) and len(order) >= 3
                and order[0] == "BUY_PRODUCT"):
            item = order[1]
            try:
                want = int(order[2])
            except (TypeError, ValueError):
                out.append(list(order))
                continue
            if item == "FERTILIZER" and not FERTILIZER_BUY:
                out.append(["BUY_PRODUCT", item, 0])
                continue
            if item == "WHEAT" and WHEAT_BUY_CAP:
                out.append(["BUY_PRODUCT", item, min(want, WHEAT_BUY_CAP)])
                continue
            out.append(list(order))
            continue
        # Outside the endgame only the fragile four are worth metering. In
        # the endgame every good is, because the dump-all orders cover
        # carrot and wheat too -- and a deep book regulates itself, since
        # the floor walk below simply allows many units when the price
        # barely moves.
        if (not isinstance(order, (list, tuple)) or len(order) < 3
                or order[0] != "SELL"
                or (order[1] not in FRAGILE and not endgame)
                or order[1] not in MARKET_PARAMS):
            out.append(list(order) if isinstance(order, (list, tuple))
                       else order)
            continue
        item = order[1]
        try:
            want = int(order[2])
        except (TypeError, ValueError):
            out.append(list(order))
            continue
        if want <= 0:
            out.append(list(order))
            continue
        if endgame:
            # Deliberately BEFORE the `tight` lift. The endgame shed is
            # always tight, so deferring to it here is what made the old
            # meter useless exactly when the dumping happens.
            inventory = inventory_of(observation, item)
            base = float(MARKET_PARAMS.get(item, {}).get(
                "base", BASE_PRICE.get(item, 1)))
            allowed = 0
            while allowed < want:
                if price_at(item, inventory + allowed) < base * SPREAD_FLOOR:
                    break
                allowed += 1
            # Never zero: a book already under the floor would otherwise
            # never be sold again and the shed would jam, which is exactly
            # how the old FLOOR failed.
            out.append(["SELL", item, max(min(want, SPREAD_MIN), allowed)])
            continue
        if tight:
            # The shed binds harder than the book: a freed slot is worth
            # more than the coins the freeing unit gives up.
            out.append(list(order))
            continue
        allowed = min(want, LOT) if LOT else want
        if FLOOR > 0.0:
            inventory = inventory_of(observation, item)
            base = float(MARKET_PARAMS.get(item, {}).get(
                "base", BASE_PRICE.get(item, 1)))
            capped = 0
            while capped < allowed:
                if price_at(item, inventory + capped) < base * FLOOR:
                    break
                capped += 1
            allowed = capped
        # A zero-quantity order is kept rather than dropped: H2's own layers
        # index into this list, and a shorter one shifts every order behind
        # it into a different slot of the ten the engine reads.
        out.append(["SELL", item, allowed])
    return out


def drain(observation: dict[str, Any], market: list) -> list:
    """Spend spare market slots selling the shed down toward DRAIN_TO."""
    if not DRAIN_TO:
        return market
    private = observation.get("private") or {}
    shed = private.get("shed") or {}
    try:
        total = sum(int(v) for v in shed.values())
    except (TypeError, ValueError):
        return market
    excess = total - DRAIN_TO
    if excess <= 0 or len(market) >= 10:
        return market

    # Sell the deepest books first: a unit of wheat costs the book almost
    # nothing where a unit of wool costs it a fiftieth of its price, so
    # draining by depth frees the same slot for the least money given up.
    held = []
    for item, count in shed.items():
        try:
            count = int(count)
        except (TypeError, ValueError):
            continue
        if count <= 0 or item not in MARKET_PARAMS:
            continue
        inventory = inventory_of(observation, item)
        base = float(MARKET_PARAMS.get(item, {}).get(
            "base", BASE_PRICE.get(item, 1)))
        room = 0
        while room < count:
            if price_at(item, inventory + room) < base * DRAIN_FLOOR:
                break
            room += 1
        if room > 0:
            held.append((room, item))
    held.sort(reverse=True)

    out = list(market)
    for room, item in held:
        if len(out) >= 10 or excess <= 0:
            break
        take = min(room, excess)
        if take > 0:
            out.append(["SELL", item, int(take)])
            excess -= take
    return out


def _seat(observation: dict[str, Any]) -> int:
    try:
        return int(observation.get("player", 0))
    except (TypeError, ValueError):
        return 0


def _busy(action: dict[str, Any], observation: dict[str, Any],
          seat: int) -> set:
    """Tiles the route's own hands are working or walking to this turn."""
    farms = observation.get("farms") or []
    if seat >= len(farms):
        return set()
    farm = farms[seat]
    units = [farm.get("farmer")] + list(farm.get("hands") or [])
    orders = [action.get("farmer")] + list(action.get("hands") or [])
    held = set()
    for spot, order in zip(units, orders):
        if not isinstance(spot, (list, tuple)) or len(spot) < 2:
            continue
        op = order[0] if isinstance(order, (list, tuple)) and order else None
        if op in MOVES_ONLY:
            continue
        held.add((int(spot[0]), int(spot[1])))
    return held


MOVES_ONLY = ("NORTH", "SOUTH", "EAST", "WEST", "PASS")


def extend(observation: dict[str, Any], action: dict[str, Any]) -> None:
    """Hire beyond the route's plan, and give those hands something to do."""
    seat = _seat(observation)
    farms = observation.get("farms") or []
    if seat >= len(farms):
        return
    farm = farms[seat]
    hands = list(farm.get("hands") or [])
    planned = list(action.get("hands") or [])

    busy = _busy(action, observation, seat)

    # Any hand the route did not write an action for is standing still.
    if EXTRA_HANDS and len(hands) > len(planned):
        planned = planned + actions_for(observation, seat, len(planned), busy)
        action["hands"] = planned

    # And any hand it told to stand still is standing still by instruction.
    if FILL_IDLE and planned:
        private = observation.get("private") or {}
        bags = private.get("inventories") or []
        tiles = farm.get("tiles") or []
        day = int(observation.get("day", 0))
        filled = list(planned)
        for index, order in enumerate(planned):
            op = order[0] if isinstance(order, (list, tuple)) and order else None
            if op != "PASS" or index >= len(hands):
                continue
            spot = hands[index]
            if not isinstance(spot, (list, tuple)) or len(spot) < 2:
                continue
            here = (int(spot[0]), int(spot[1]))
            carrying = bags[index + 1] if index + 1 < len(bags) else {}
            found = actions_for(observation, seat, index, busy)
            if found:
                filled[index] = found[0]
        action["hands"] = filled

    if not EXTRA_HANDS:
        return
    step = int(observation.get("step", 0))
    if step % 24 > HIRE_BEFORE_HOUR:
        return
    try:
        money = float(farm.get("money", 0.0) or 0.0)
    except (TypeError, ValueError):
        return
    market = action.setdefault("market", [])
    already = sum(1 for o in market
                  if isinstance(o, (list, tuple)) and o and o[0] == "HIRE")
    # The route's own hires come out of the same fibonacci curve, so its
    # orders are counted before ours and ours are appended behind them.
    want = EXTRA_HANDS - already
    hires_today = int(farm.get("hires_today", 0) or 0)
    cost = 0.0
    a, b = 1, 1
    for _ in range(hires_today):
        a, b = b, a + b
    for _ in range(max(0, want)):
        if len(market) >= 10 or money - cost - a < HIRE_RESERVE:
            break
        market.append(["HIRE"])
        cost += a
        a, b = b, a + b


def agent(observation: dict[str, Any], configuration: Any = None):
    """Entry point. Must stay the last callable defined in this module."""
    step = int(observation.get("step", 0) or 0)
    if SPLICE and step >= SPLICE:
        return _reactive.agent(observation, configuration)
    # The route is driven every step up to the splice, because it is a
    # recorded programme and skipping a step leaves its hands somewhere it
    # does not expect them.
    action = _core.agent(observation, configuration)
    try:
        if isinstance(action, dict):
            if action.get("market"):
                action["market"] = meter(observation, action["market"])
            extend(observation, action)
            # After extend, so the route's own orders and its hires both
            # keep their slots and the drain only takes what is left.
            action["market"] = drain(observation, action.get("market") or [])
    except Exception:
        return action
    return action
