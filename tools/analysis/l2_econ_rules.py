"""Verify every decision-relevant Kaggriculture rule against the stock engine.

Each check puts the game in a chosen state (tools/analysis/l2_econ_sim.Sim,
which drives kaggriculture.interpreter directly), submits exact actions and
reads back what the engine did. Prints one line per rule with the measured
value, and writes rl/data/l2/econ/rules.json. Line numbers refer to
.conda/Lib/site-packages/kaggle_environments/envs/kaggriculture/kaggriculture.py
(kaggle-environments 1.32.7).

    python -m tools.analysis.l2_econ_rules
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import kaggle_environments.envs.kaggriculture.kaggriculture as E  # noqa: E402
from tools.analysis.l2_econ_sim import Sim  # noqa: E402

OUT = ROOT / "rl" / "data" / "l2" / "econ" / "rules.json"
RESULTS: list[dict] = []
WEED = {"kind": "WEED"}


def check(name: str, lines: str, measured, ok: bool) -> None:
    RESULTS.append({"rule": name, "lines": lines, "measured": measured, "ok": bool(ok)})
    print(f"[{'PASS' if ok else 'FAIL'}] {name}  (L{lines})\n        {measured}")


def P(**kw):
    return {"farmer": kw.get("farmer", ["PASS"]), "hands": kw.get("hands", []),
            "market": kw.get("market", [])}


# ---------------------------------------------------------------------------
def turn_order():
    s = Sim()
    s.carry(0, "WHEAT", 5)
    m0 = s.farm(0)["money"]
    s.step(P(farmer=["DROP"], market=[["SELL", "WHEAT", 5]]))
    got = s.farm(0)["money"] - m0
    check("Unit actions run before the market: DROP and SELL of the same goods in one turn",
          "935-941", f"money +{got:.0f} for 5 wheat dropped and sold in one turn; shed now "
          f"{s.private(0)['shed']['WHEAT']}", got > 0 and s.private(0)["shed"]["WHEAT"] == 0)

    s = Sim()
    s.to_day(0, 23)
    s.carry(0, "WHEAT", 3)
    s.step(P(market=[["SELL", "WHEAT", 3]]))
    check("End-of-day drop happens after the market: carried goods cannot be sold that turn",
          "941-946, 843-857", f"sold 0 at hour 23, shed next morning = {s.private(0)['shed']['WHEAT']}",
          s.private(0)["shed"]["WHEAT"] == 3)


def hiring():
    s = Sim()
    s.step(P(hands=[["WEST"]], market=[["HIRE"]]))
    pos0 = list(s.farm(0)["hands"][0])
    s.step(P(hands=[["WEST"]]))
    pos1 = list(s.farm(0)["hands"][0])
    check("A hand hired this turn cannot act this turn (market runs after unit actions)",
          "935-941, 702-709", f"hand spawned at {pos0}, ignored its same-turn WEST; next turn at {pos1}",
          pos0 == [5, 4] and pos1 == [4, 4])

    s = Sim()
    m0 = s.farm(0)["money"]
    s.step(P(market=[["HIRE"]] * 12))
    n1 = len(s.farm(0)["hands"])
    spent1 = m0 - s.farm(0)["money"]
    spawns = [tuple(h) for h in s.farm(0)["hands"]]
    s.step(P(market=[["HIRE"]] * 2))
    spent2 = m0 - s.farm(0)["money"]
    check("Max 10 market orders per turn (extras silently dropped); hire cost fib(n)",
          "560, 690-709", f"12 HIREs -> {n1} hands for {spent1:.0f}; 2 more next turn -> total "
          f"{spent2:.0f} (1+1+2+3+5+8+13+21+34+55=143, +89+144=376)",
          n1 == 10 and spent1 == 143 and spent2 == 376)
    check("Spawn tiles: least-occupied shed-access tile, NWSE order; 1st hire lands on (5,4)",
          "533-541", f"first 10 spawns {spawns}", spawns[0] == (5, 4))

    costs = [E._hire_cost(n) for n in range(16)]
    check("Hire cost table (n-th hire of the day)", "690-699", f"{costs}", costs[:5] == [1, 1, 2, 3, 5])

    s = Sim()
    s.to_day(1)
    s.step(P(market=[["HIRE"]]))
    check("Hires reset nightly: first hire of a new day costs 1 again",
          "879-882", f"hires_today={s.farm(0)['hires_today']}, money {s.farm(0)['money']:.0f}",
          s.farm(0)["money"] == 2999)


def market_rules():
    base = {it: E.market_price(it, 10000) for it in E.PRODUCTS}
    check("Base prices at I0=10000", "41-51, 192-206", f"{base}", base["WHEAT"] == 25)

    # Same slot: lockstep, equal quotes.
    s = Sim()
    s.private(0)["shed"]["WHEAT"] = 10
    s.private(1)["shed"]["WHEAT"] = 10
    m = [s.farm(i)["money"] for i in (0, 1)]
    s.step(P(market=[["SELL", "WHEAT", 10]]), P(market=[["SELL", "WHEAT", 10]]))
    g = [s.farm(i)["money"] - m[i] for i in (0, 1)]
    inv = s.market["inventory"]["WHEAT"]
    check("Same slot, same item: both players get the same quote per unit (lockstep), +2 inventory per round",
          "583-626", f"p0 +{g[0]:.0f}, p1 +{g[1]:.0f}; wheat inventory {inv} (10000 +20 -1 town centre)",
          g[0] == g[1] and inv == 10019)

    # Different slots: the earlier slot sells first.
    for size in (10, 40):
        for item in ("WHEAT", "MILK", "STRAWBERRY", "MELON", "FERTILIZER"):
            s = Sim()
            s.private(0)["shed"][item] = size
            s.private(1)["shed"][item] = size
            m = [s.farm(i)["money"] for i in (0, 1)]
            s.step(P(market=[["SELL", item, size]]),
                   P(market=[["BUY_SEED", "WHEAT", 1], ["SELL", item, size]]))
            g = [s.farm(0)["money"] - m[0], s.farm(1)["money"] - m[1] + 10]
            check(f"Earlier slot wins: {size} {item} each, p0 in slot 0, p1 in slot 1",
                  "563-626", f"p0 +{g[0]:.0f}, p1 +{g[1]:.0f}, first-slot edge {g[0] - g[1]:.0f}",
                  g[0] >= g[1])

    # Floor sales do not add inventory.
    s = Sim()
    x = 10000
    while E.market_price("MELON", x) > 1:
        x += 1
    s.market["inventory"]["MELON"] = x + 5
    s.private(0)["shed"]["MELON"] = 3
    m0 = s.farm(0)["money"]
    s.step(P(market=[["SELL", "MELON", 3]]))
    check("A sale at the $1 floor pays $1 and does not add market inventory",
          "657-660", f"melon floor starts at inventory {x}; sold 3 for {s.farm(0)['money'] - m0:.0f}, "
          f"inventory {x + 5} -> {s.market['inventory']['MELON']} (the -1 is the town centre)",
          s.market["inventory"]["MELON"] == x + 4)

    # Buy quoted at post-buy inventory.
    s = Sim()
    m0 = s.farm(0)["money"]
    s.step(P(market=[["BUY_PRODUCT", "WHEAT", 1], ["SELL", "WHEAT", 1]]))
    check("Buy quoted at post-buy inventory, sell at pre-sell: an isolated round trip nets 0",
          "598-601, 652-672", f"buy+sell 1 wheat net {s.farm(0)['money'] - m0:+.0f}; buy price "
          f"{E.market_price('WHEAT', 9999)}", s.farm(0)["money"] == m0)

    s = Sim()
    m0 = s.farm(0)["money"]
    s.step(P(market=[["BUY_PRODUCT", "WHEAT", 100]]))
    paid = m0 - s.farm(0)["money"]
    check("Buying 100 wheat at I0 (price climbs sqrt-steeply below I0)", "598-601",
          f"paid {paid:.0f} (avg {paid / 100:.2f}); price now {E.market_price('WHEAT', s.market['inventory']['WHEAT'])}",
          paid > 2500)

    s = Sim()
    s.private(0)["shed"]["GOOSE"] = 1
    s.step(P(market=[["SELL", "GOOSE", 1], ["SELL", "FERTILIZER", 1],
                     ["BUY_PRODUCT", "MILK", 1]]))
    check("SELL only for the 9 products (fertilizer included; animals cannot be sold); "
          "BUY_PRODUCT only wheat and fertilizer", "596-607",
          f"goose still in shed: {s.private(0)['shed']['GOOSE']}; milk bought: {s.private(0)['shed']['MILK']}",
          s.private(0)["shed"]["GOOSE"] == 1 and s.private(0)["shed"]["MILK"] == 0)

    s = Sim()
    s.farm(0)["money"] = 250
    s.step(P(market=[["BUY_SEED", "STRAWBERRY", 5], ["BUY_SEED", "WHEAT", 1]]))
    check("Running out of money stops that order mid-way; later orders still run",
          "618-623, 673-678", f"strawberry seeds {s.private(0)['seeds']['STRAWBERRY']}, wheat seeds "
          f"{s.private(0)['seeds']['WHEAT']}, money {s.farm(0)['money']:.0f}",
          s.private(0)["seeds"]["STRAWBERRY"] == 2 and s.private(0)["seeds"]["WHEAT"] == 1)


def same_turn_chains():
    s = Sim()
    s.to_day(4)
    t = s.put_plant(0, 4, 4, "WHEAT", 0)
    t["yield_units"] = 4
    s.farm(0)["hands"] = [[4, 4], [4, 4]]
    s.private(0)["inventories"] = [{}, {}, {}]
    s.private(0)["seeds"]["WHEAT"] = 1
    s.step(P(farmer=["HARVEST"], hands=[["PLANT", "WHEAT"], ["WATER"]]))
    t = s.tile(0, 4, 4)
    check("Units act one after another within a turn: HARVEST (farmer), PLANT (hand 1), WATER (hand 2) "
          "on one tile in the same turn all apply", "935-939",
          f"harvested {s.private(0)['inventories'][0].get('WHEAT')}, new plant day {t['planted_day']} "
          f"watered {t['watered_today']}", t["planted_day"] == 4 and t["watered_today"])

    s = Sim()
    s.step(P(farmer=["PLANT", "WHEAT"], market=[["BUY_SEED", "WHEAT", 1]]))
    t_same = s.tile(0, 4, 4)
    s.step(P(farmer=["PLANT", "WHEAT"]))
    check("Seeds bought this turn cannot be planted this turn (market runs after unit actions)",
          "935-941, 673-678", f"same-turn PLANT -> {t_same}; next turn -> {s.tile(0, 4, 4)['crop']}",
          t_same is None and s.tile(0, 4, 4)["crop"] == "WHEAT")

    for order in (["SELL", "HIRE"], ["HIRE", "SELL"]):
        s = Sim()
        s.farm(0)["money"] = 0
        s.private(0)["shed"]["WHEAT"] = 1
        orders = [["SELL", "WHEAT", 1] if o == "SELL" else ["HIRE"] for o in order]
        s.step(P(market=orders))
        check(f"Own orders run in list order: {order} with $0 in the bank", "563-581, 702-705",
              f"hands hired {len(s.farm(0)['hands'])}, money {s.farm(0)['money']:.0f}", True)


def shed_rules():
    s = Sim()
    s.private(0)["shed"]["WHEAT"] = 100
    s.step(P(market=[["BUY_PRODUCT", "WHEAT", 1], ["BUY_ANIMAL", "GOOSE", 1],
                     ["BUY_SEED", "WHEAT", 1]]))
    check("Full shed (100) blocks BUY_PRODUCT and BUY_ANIMAL, not BUY_SEED",
          "662-686", f"shed wheat {s.private(0)['shed']['WHEAT']}, geese {s.private(0)['shed']['GOOSE']}, "
          f"seeds {s.private(0)['seeds']['WHEAT']}",
          s.private(0)["shed"]["WHEAT"] == 100 and s.private(0)["shed"]["GOOSE"] == 0
          and s.private(0)["seeds"]["WHEAT"] == 1)

    s = Sim()
    s.private(0)["shed"]["WHEAT"] = 98
    s.carry(0, "MILK", 5)
    s.step(P(farmer=["DROP"]))
    check("DROP stores what fits and DISCARDS the rest of the carried stack",
          "343-356", f"shed milk {s.private(0)['shed']['MILK']}, carried left "
          f"{s.private(0)['inventories'][0]}", s.private(0)["shed"]["MILK"] == 2
          and not s.private(0)["inventories"][0])

    s = Sim()
    s.private(0)["shed"]["WHEAT"] = 98
    s.carry(0, "MILK", 5)
    s.step(P(farmer=["PLACE", "MILK", 5]))
    check("PLACE <item> n into the shed stores what fits and KEEPS the rest in hand",
          "393-410", f"shed milk {s.private(0)['shed']['MILK']}, carried {s.private(0)['inventories'][0]}",
          s.private(0)["shed"]["MILK"] == 2 and s.private(0)["inventories"][0].get("MILK") == 3)

    s = Sim()
    s.private(0)["shed"]["WHEAT"] = 60
    s.private(0)["shed"]["COW"] = 40
    s.step(P(market=[["BUY_PRODUCT", "WHEAT", 1]]))
    check("Animals waiting in the shed count toward the 100 cap", "667, 682",
          f"wheat {s.private(0)['shed']['WHEAT']} (buy refused)", s.private(0)["shed"]["WHEAT"] == 60)

    s = Sim()
    s.to_day(0, 23)
    s.private(0)["shed"]["WHEAT"] = 97
    s.carry(0, "EGG", 5)
    s.step()
    check("End-of-day drop discards overflow (hands' inventories included)", "843-857",
          f"eggs in shed next morning {s.private(0)['shed']['EGG']} of 5", s.private(0)["shed"]["EGG"] == 3)


def planting_rules():
    s = Sim()
    s.private(0)["seeds"]["MELON"] = 1
    s.step(P(market=[["HIRE"]]))
    s.move_farmer(0, 0, 0)
    s.farm(0)["hands"][0] = [1, 0]
    s.step(P(farmer=["PLANT", "MELON"], hands=[["PLANT", "MELON"]]))
    check("More PLANT <crop> than seeds in one turn cancels EVERY plant of that crop",
          "920-933", f"tiles {s.tile(0, 0, 0)}, {s.tile(0, 1, 0)}; seeds left {s.private(0)['seeds']['MELON']}",
          s.tile(0, 0, 0) is None and s.private(0)["seeds"]["MELON"] == 1)

    s = Sim()
    s.private(0)["seeds"]["WHEAT"] = 1
    s.move_farmer(0, 0, 0)
    s.step(P(farmer=["PLANT", "WHEAT"]))
    s.to_day(1)
    check("Planting day counts as unwatered: a seed not watered that day is a weed by morning",
          "222, 777-785", f"tile next morning {s.tile(0, 0, 0)}", s.tile(0, 0, 0) == WEED)

    s = Sim()
    s.put_plant(0, 0, 0, "WHEAT", 0)
    s.move_farmer(0, 0, 0)
    s.step(P(farmer=["WATER"]))
    s.to_day(2)
    alive_d2 = isinstance(s.tile(0, 0, 0), dict) and s.tile(0, 0, 0).get("kind") == "PLANT"
    s.to_day(3)
    check("One unwatered day is survivable; the second consecutive one kills the plant",
          "777-785", f"alive at day 2: {alive_d2}; day 3: {s.tile(0, 0, 0)}",
          alive_d2 and s.tile(0, 0, 0) == WEED)

    s = Sim()
    s.move_farmer(0, 5, 5)
    s.private(0)["seeds"]["WHEAT"] = 1
    s.step(P(farmer=["PLANT", "WHEAT"]))
    s.step(P(farmer=["NORTH"]))
    check("Locked tiles are passable but every tile action there is a no-op (seed kept)",
          "323-332, 414-415", f"tile {s.tile(0, 5, 5)}, seeds {s.private(0)['seeds']['WHEAT']}, "
          f"farmer now {s.farm(0)['farmer']}", s.tile(0, 5, 5) == "LOCKED"
          and s.private(0)["seeds"]["WHEAT"] == 1)

    s = Sim()
    s.private(0)["shed"]["WHEAT"] = 4
    s.move_farmer(0, 5, 5)
    s.step(P(farmer=["PICKUP", "WHEAT", 4]))
    check("PICKUP/DROP/PLACE work from a LOCKED shed-access tile", "339-410",
          f"carried {s.private(0)['inventories'][0]}", s.private(0)["inventories"][0].get("WHEAT") == 4)


def one_time_yields():
    def grow(crop, water_ages, fert_age=None, harvest_age=None, fert_after_water=False):
        s = Sim()
        s.put_plant(0, 4, 4, crop, 0)
        last = harvest_age if harvest_age is not None else max(water_ages)
        for d in range(last + 1):
            s.to_day(d)
            s.private(0)["inventories"][0]["FERTILIZER"] = 1
            acts = []
            if fert_age == d and not fert_after_water:
                acts.append(["FERTILIZE"])
            if d in water_ages:
                acts.append(["WATER"])
            if fert_age == d and fert_after_water:
                acts.append(["FERTILIZE"])
            if harvest_age == d:
                acts.append(["HARVEST"])
            for a in acts:
                s.step(P(farmer=a))
        t = s.tile(0, 4, 4)
        if harvest_age is not None:
            return s.private(0)["inventories"][0].get(crop, 0)
        return t.get("yield_units") if isinstance(t, dict) else t

    all_days = {"WHEAT": [0, 2, 3, 4], "CARROT": [0, 2, 3], "MELON": [0, 2, 4, 6, 7, 8, 9, 10]}
    for crop, days in all_days.items():
        cd = E.CROPS[crop]
        window = ((cd["max_yield_day"] + 1) // 2, cd["max_yield_day"])
        plain = grow(crop, days)
        by_fert = {a: grow(crop, days, fert_age=a) for a in range(0, cd["max_yield_day"] + 1)}
        check(f"{crop}: window ages {window[0]}-{window[1]}; yield with survival+window water, "
              f"and with one fertilizer applied at each age",
              "431-444, 475-482", f"no fert {plain}; fert at age -> yield {by_fert}", True)
    w_late = grow("WHEAT", [0, 2, 3, 4], fert_age=4, fert_after_water=True)
    w_early = grow("WHEAT", [0, 2, 3, 4], fert_age=4)
    check("Fertilizer applied AFTER that day's water does not boost that day (bonus read at WATER time)",
          "442", f"wheat fertilized at age 4 after its water: {w_late}; before its water: {w_early}",
          w_late == 4 and w_early == 5)
    early = grow("WHEAT", [0], harvest_age=1)
    check("HARVEST before first_yield_day is a silent no-op (wheat/carrot age<2, melon age<10)",
          "453-463", f"wheat harvested at age 1 -> {early} units", early == 0)
    ages = {h: grow("WHEAT", [d for d in (0, 2, 3, 4) if d <= h], harvest_age=h) for h in (2, 3, 4)}
    check("Wheat harvested at age 2/3/4 with every window watering", "431-473", f"{ages}", ages[4] == 4)

    # Same-step order: unit order is farmer, then hands in list order.
    s = Sim()
    s.to_day(2)
    s.put_plant(0, 4, 4, "WHEAT", 0)
    s.farm(0)["hands"] = [[4, 4]]
    s.private(0)["inventories"] = [{}, {"FERTILIZER": 1}]
    s.step(P(farmer=["WATER"], hands=[["FERTILIZE"]]))
    y_bad = s.tile(0, 4, 4)["yield_units"]
    check("Within one turn units act in order farmer, hand1, hand2...: water by the farmer "
          "then fertilize by a hand misses that day's double", "935-939",
          f"yield after (farmer WATER, hand FERTILIZE) at age 2: {y_bad} (2 = single bonus)", y_bad == 2)


def decay_rules():
    s = Sim()
    t = s.put_plant(0, 0, 0, "WHEAT", 0)
    t["yield_units"] = 4
    mls = t["max_lifespan_step"]
    trail = []
    while True:
        tile = s.tile(0, 0, 0)
        if s.step_no % 24 == 23 and isinstance(tile, dict) and tile.get("kind") == "PLANT":
            tile["watered_today"] = True
        trail.append((s.step_no, tile.get("yield_units") if isinstance(tile, dict) and tile.get("kind") == "PLANT" else "WEED"))
        if not (isinstance(tile, dict) and tile.get("kind") == "PLANT") or s.step_no > mls + 20:
            break
        s.step()
    around = [x for x in trail if x[0] >= mls - 1]
    check("One-time decay: max_lifespan_step = (planted+max_yield_day+1)*24; -1 unit at that step "
          "(after that turn's actions) and every 2nd step after; weed at 0",
          "224, 752-766", f"wheat planted day 0, mls={mls}; (step, units before that step runs) {around}",
          around[1] == (mls, 4) and around[2] == (mls + 1, 3) and around[-1][1] == "WEED")

    s = Sim()
    t = s.put_plant(0, 4, 4, "WHEAT", 0)
    t["yield_units"] = 4
    while s.step_no < mls:
        if s.step_no % 24 == 23:
            s.tile(0, 4, 4)["watered_today"] = True
        s.step()
    s.step(P(farmer=["HARVEST"]))
    got = s.private(0)["inventories"][0].get("WHEAT", 0)
    check("Harvest at age max_yield_day+1, hour 0 still gets the full yield", "944, 752-766",
          f"wheat harvested at step {mls} (age 5 hour 0): {got}", got == 4)


def ongoing_yields():
    def tomato(crop, water_days, fert_days, harvest_days, until):
        s = Sim()
        s.put_plant(0, 4, 4, crop, 0)
        got, units = 0, []
        for d in range(until + 1):
            s.to_day(d)
            s.private(0)["inventories"][0]["FERTILIZER"] = 1
            if d in fert_days:
                s.step(P(farmer=["FERTILIZE"]))
            if d in water_days:
                s.step(P(farmer=["WATER"]))
            t = s.tile(0, 4, 4)
            units.append(t.get("yield_units") if isinstance(t, dict) and t.get("kind") == "PLANT" else "W")
            if d in harvest_days:
                before = s.private(0)["inventories"][0].get(crop, 0)
                s.step(P(farmer=["HARVEST"]))
                got += s.private(0)["inventories"][0].get(crop, 0) - before
        return got, units

    every_other = list(range(0, 18, 2))
    g, u = tomato("TOMATO", every_other, [], [11], 12)
    check("Tomato, survival water only (every other day): 1 unit credited per night from age 8 to 11",
          "769-802", f"harvested {g}; units on tile by day {u}", g == 4)
    g, u = tomato("TOMATO", every_other + [7, 9], [7], [9, 11], 12)
    check("Tomato, one fertilizer on day 7 + water on 7,8,9: nights 7,8,9 doubled",
          "798-800, 481", f"harvested {g}; units by day {u}", g == 7)
    g, u = tomato("TOMATO", every_other + [7, 9], [7, 10], [9, 11], 12)
    check("Tomato, fertilizer on days 7 and 10: all 4 productions doubled (cap 4 held: harvest by age 9)",
          "798-800", f"harvested {g}; units by day {u}", g == 8)
    g, u = tomato("TOMATO", every_other + [7, 9], [7, 10], [11], 12)
    check("Tomato held cap is 4: doubled production left unharvested is lost", "800",
          f"harvested {g} (one harvest at age 11); units by day {u}", g == 4)
    g, u = tomato("STRAWBERRY", every_other, [], [16], 17)
    check("Strawberry, survival water: productions on nights 9, 11, 13, 15 (ages 10,12,14,16)",
          "769-802", f"harvested {g}; units by day {u}", g == 4)
    g, u = tomato("STRAWBERRY", every_other + [9, 11, 13, 15], [9, 13], [12, 16], 17)
    check("Strawberry, fertilizer on days 9 and 13 + water on 9,11,13,15: all 4 doubled",
          "798-800", f"harvested {g}; units by day {u}", g == 8)
    g, u = tomato("TOMATO", every_other, [], [11], 14)
    check("Ongoing decay starts the day after the 4th production; empty plant becomes a weed at once",
          "801-802, 752-766", f"tomato units by day {u}", u[12] == "W")


def animal_rules():
    def herd(animal, days, feed=True, care=True, feed_days=None, care_days=None, harvest=False):
        s = Sim()
        s.put_animal(0, 4, 4, animal, 0)
        seen, got = [], 0
        for d in range(days):
            s.to_day(d)
            s.private(0)["inventories"][0]["WHEAT"] = 1
            t = s.tile(0, 4, 4)
            seen.append(t.get("yield_units") if "animal" in t else "ESC")
            if "animal" not in t:
                continue
            if harvest and t["yield_units"]:
                b = sum(s.private(0)["inventories"][0].values())
                s.step(P(farmer=["HARVEST"]))
                got += sum(s.private(0)["inventories"][0].values()) - b
            if feed and (feed_days is None or d in feed_days):
                s.step(P(farmer=["FEED"]))
            if care and (care_days is None or d in care_days):
                s.step(P(farmer=["CARE"]))
        return seen, got

    for animal, days in (("GOOSE", 10), ("COW", 14), ("SHEEP", 13)):
        seen, got = herd(animal, days, harvest=True)
        seen_nc, got_nc = herd(animal, days, care=False, harvest=True)
        check(f"{animal}: fed+cared daily from placement vs fed only (units on tile each morning "
              f"before harvest; harvested daily)", "805-833",
              f"care: {seen} total {got}; no care: {seen_nc} total {got_nc}", True)

    seen, _ = herd("COW", 14, harvest=False)
    check("Cow first production with 7 banked cares requests 8 but max_held 6 caps it", "827",
          f"cow units by morning {seen}", max(x for x in seen if x != "ESC") == 6)

    seen, _ = herd("GOOSE", 8, feed_days={0, 1, 2}, care_days={0, 1, 2})
    check("Unfed on the production night: base 1 still credited, banked care forfeited",
          "824-828", f"goose fed+cared days 0-2 only, units by morning {seen}", seen[4] == 1)

    seen, _ = herd("GOOSE", 4, feed=False, care=False)
    check("New animal survives its first unfed day; escapes after the 2nd consecutive unfed night",
          "236, 813-820", f"goose never fed, by morning {seen}", seen[1] == 0 and seen[2] == "ESC")

    s = Sim()
    s.put_animal(0, 4, 4, "COW", 0)
    s.to_day(1)
    s.tile(0, 4, 4)["fed_today"] = True
    a1 = s.tile(0, 4, 4)["fertilizer_available"]
    s.to_day(3)
    s.step(P(farmer=["COLLECT_FERTILIZER"]))
    s.step(P(farmer=["COLLECT_FERTILIZER"]))
    got = s.private(0)["inventories"][0].get("FERTILIZER", 0)
    check("Fertilizer: every surviving animal (fed or not) gets 1 available per night; it does not stack",
          "831, 515-522", f"available day 1: {a1}; collected twice on day 3 after 3 nights: {got}",
          a1 and got == 1)

    s = Sim()
    s.put_animal(0, 0, 0, "COW", 0)
    s.move_farmer(0, 0, 0)
    s.step(P(farmer=["DIG"]))
    check("DIG cannot remove a structure with an animal on it", "484-491",
          f"tile kind {s.tile(0, 0, 0)['kind']} animal {s.tile(0, 0, 0).get('animal')}",
          s.tile(0, 0, 0).get("animal") == "COW")


def town_rules():
    s = Sim()
    s.step()
    inv0 = dict(s.market["inventory"])
    s.run_to(4)
    inv4 = dict(s.market["inventory"])
    check("Town centre eats 1 of each product (not fertilizer) at every hour 0, after the market",
          "728-749", f"after step 0: wheat {inv0['WHEAT']}, fert {inv0['FERTILIZER']}; "
          f"no shops yet, step 4: wheat {inv4['WHEAT']}", inv0["WHEAT"] == 9999 and inv0["FERTILIZER"] == 10000)

    s = Sim(seed=11)
    unlock = []
    for d in range(30):
        s.to_day(d)
        unlock.append(len(s.obs.town["unlocked_shops"]))
    first = [d for d in range(1, 30) if unlock[d] > unlock[d - 1]]
    check("Shops unlock on the night before days 3,6,...,24 (8 max), drawn with replacement",
          "884-891", f"days a new shop is live from: {first}", first == [3, 6, 9, 12, 15, 18, 21, 24])

    shops = []
    for fill in (False, True):
        s = Sim(seed=12345)
        if fill:
            for y in range(5):
                for x in range(5):
                    s.farm(0)["tiles"][y][x] = {"kind": "WEED"}
        s.to_day(3)
        shops.append(s.obs.town["unlocked_shops"][0])
    check("The shop draw shares the weed RNG: the number of EMPTY tiles on both farms that night "
          "changes which shop unlocks (same seed)", "870-891, 836-840",
          f"seed 12345 day-3 shop with an empty farm: {shops[0]}; with a full farm: {shops[1]}", True)

    # Weed spawn rate.
    total = spawned = 0
    for seed in range(1, 41):
        s = Sim(seed=seed)
        for d in range(1, 30):
            s.to_day(d)
        for i in (0, 1):
            spawned += sum(1 for row in s.farm(i)["tiles"] for t in row if t == WEED)
            total += 25 * 29
    check("Weeds: each EMPTY unlocked tile has a 0.5% chance per night", "836-840",
          f"measured {spawned}/{total} tile-nights = {spawned / total:.4f}", 0.003 < spawned / total < 0.007)


def episode_length():
    from kaggle_environments import make
    seen = []

    def agent(obs):
        seen.append((obs.get("step"), obs.get("day"), obs.get("hour")))
        return {"farmer": ["PASS"], "hands": [], "market": []}

    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 3})
    env.run([agent, "pass"])
    last = seen[-1]
    check("A game is 719 agent turns: steps 0..718; day 29 has only hours 0-22; day 29's "
          "end-of-day refresh never runs", "945-963",
          f"agent called {len(seen)} times, last (step, day, hour) = {last}; records {len(env.steps)}",
          len(seen) == 719 and last == (718, 29, 22))


def main() -> None:
    for fn in (turn_order, hiring, market_rules, same_turn_chains, shed_rules, planting_rules, one_time_yields,
               decay_rules, ongoing_yields, animal_rules, town_rules, episode_length):
        try:
            fn()
        except Exception as error:
            check(f"{fn.__name__} crashed", "-", f"{type(error).__name__}: {error}", False)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(RESULTS, indent=1, default=str), encoding="utf-8")
    bad = [r for r in RESULTS if not r["ok"]]
    print(f"\n{len(RESULTS) - len(bad)}/{len(RESULTS)} checks pass; wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
