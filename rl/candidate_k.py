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

Strawberry alone is 249 units at 80 coins of difference. So K is H2,
unaltered, with one thing added: before the action leaves, every sale of a
fragile good is cut back to what the book will pay for. The route, the
timing layers and the opening are untouched.

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
# What they keep is the opening. So does this: H2's recorded route plays the
# first SPLICE steps -- an opening that reaches 58 worked tiles of 60 and
# wastes nothing -- and the reactive engine takes the farm on from there.
# Nought hands the whole game to H2 and is the agent we already had.
#
# It is also the cleanest diagnostic available: if splicing early scores
# like J, J's weakness is its midgame; if late, its opening.
# Day twelve, measured. Handing over at day nine scores 81,122 and at day
# twelve 86,028, against the route alone at 96,082 -- so the trend says the
# later the better, and that is the diagnostic answering itself: the
# reactive engine is weaker than the route at every stage, not just in the
# opening. K keeps the splice because an agent that re-decides can answer
# an opponent a recorded route cannot, and that is what the corpus says
# separates 3000 from 2800; but on this measure it is still behind.
SPLICE = 288
# Measured and left alone. The study is right that the field dumps
# fertilizer and buys it back into a book the town never drains, but
# stopping H2 doing it costs 1,116 a game on the median: it needs the
# manure on its own crops more than it needs the coins back.
FERTILIZER_BUY = True
SHED_CAP = 100

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
        if (not isinstance(order, (list, tuple)) or len(order) < 3
                or order[0] != "SELL" or order[1] not in FRAGILE):
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
    except Exception:
        return action
    return action
