"""Candidate H‑D – demand‑timed, denial‑sensitive, adaptive agent.

This agent is the strongest from our analysis of the top 100 Kaggle agents.
It reads the town's unlocked shops, computes remaining demand and its rate,
and plans production to maximise revenue while suppressing opponent prices.
Planting is timed to align with the demand window, ensuring crops enter the
market when prices are highest.

Author: Auto‑generated for the user.
"""

from __future__ import annotations

import math
from collections import Counter
from typing import Any

from core.routing import distance, step_toward
from rl.demand import remaining_demand, demand_rate, SHOPS
from rl.market import MARKET_PARAMS, inventory_of, price_at, sale_revenue
from rl.economics import (
    water_value, fertilize_value, harvest_value, feed_value,
    care_value, collect_fertilizer_value, plant_value,
    crop_can_mature, CROPS,
)
from rl.runtime import AgentAction

TRAVEL_EXPONENT = 2.5
OPENING_LAND_DAY = 5        
OPENING_HIRES = 4           
HAND_CAP = 11              
WHEAT_PER_BIRD = 0.8      
EMERGENCY_FLOOR = 130.0       
MAX_QUADRANTS = 3
SELL_PACE = 0.7              
LAST_DAY = 29
HARVEST_HOLD = True          

# Crop book depths (units until price floor)
CROP_DEPTH = {
    "CARROT": 842,
    "TOMATO": 529,
    "STRAWBERRY": 62,
    "MELON": 158,
    "WHEAT": 10,
}
ANIMAL_PRODUCTS = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}
ANIMAL_COSTS = {"GOOSE": 300, "COW": 400, "SHEEP": 500}
ANIMAL_STRUCTURES = {"GOOSE": "COOP", "COW": "PASTURE", "SHEEP": "PASTURE"}
PASS = ["PASS"]


# ---------- Helper functions ----------
def _farm(obs):
    player = obs.get("player", 0)
    farms = obs.get("farms", [])
    if player < len(farms):
        return farms[player]
    return {}


def _positions(farm):
    units = [farm.get("farmer")] + farm.get("hands", [])
    return [tuple(p) if isinstance(p, (list, tuple)) else (0, 0) for p in units]


def _inventory(obs, worker):
    invs = obs.get("private", {}).get("inventories", [])
    if worker < len(invs):
        return invs[worker]
    return {}


def _shed(obs):
    return obs.get("private", {}).get("shed", {})


def _seeds(obs):
    return obs.get("private", {}).get("seeds", {})


def _shed_tiles(board_size=10):
    half = board_size // 2
    return [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]


def _shed_adjacent(x, y, board_size=10):
    return (x, y) in set(_shed_tiles(board_size))


def _owned(tiles, x, y):
    return 0 <= y < len(tiles) and 0 <= x < len(tiles[y]) and tiles[y][x] != "LOCKED"


def _tile_at(farm, pos):
    x, y = pos
    return farm["tiles"][y][x] if 0 <= y < len(farm["tiles"]) and 0 <= x < len(farm["tiles"][y]) else None


def fertilizer_gain(tile, day):
    """Extra units this tile would yield if manure went on it today.
    Copied from Candidate G's verified implementation.
    """
    if tile.get("fertilized_until_day", -1) >= day:
        return 0
    spec = CROPS.get(str(tile.get("crop", "")))
    if spec is None:
        return 0
    held = int(tile.get("yield_units", 0) or 0)
    planted = int(tile.get("planted_day", day))
    if spec["ongoing"]:
        interval = max(1, int(spec["interval"]))
        gain = 0
        for ahead in (0, 1, 2):
            since = (day + ahead) - planted - int(spec["first"])
            if since >= 0 and since % interval == 0:
                gain += 1
        return max(0, min(gain, int(spec["max_yield"]) - held))
    age = day - planted
    start = (int(spec["max_day"]) + 1) // 2
    last = int(spec["max_day"])
    if age > last:
        return 0
    remaining = last - max(age, start) + 1
    if remaining <= 0:
        return 0
    room = int(spec["max_yield"]) - held - remaining
    return max(0, min(room, min(3, remaining)))


def census(tiles):
    """Count everything we need for scheduling in one pass."""
    out = {
        "geese": 0, "cows": 0, "sheep": 0,
        "animals": 0,
        "empty_coops": 0, "empty_pastures": 0,
        "wheat": 0, "crop_wheat": 0,
        "crop_carrot": 0, "crop_tomato": 0, "crop_strawberry": 0, "crop_melon": 0,
        "free": 0,
        "unfed": 0, "uncared": 0,
        "manure": 0,
        "ripe_crop_units": 0, "ripe_animal_units": 0,
        "dry": 0,
        "unwatered_plants": 0,
    }
    for row in tiles:
        for tile in row:
            if tile == "LOCKED":
                continue
            if tile is None:
                out["free"] += 1
                continue
            if not isinstance(tile, dict):
                continue
            if "animal" in tile:
                out["animals"] += 1
                animal = tile.get("animal", "")
                if animal == "GOOSE":
                    out["geese"] += 1
                elif animal == "COW":
                    out["cows"] += 1
                elif animal == "SHEEP":
                    out["sheep"] += 1
                if not tile.get("fed_today"):
                    out["unfed"] += 1
                if not tile.get("cared_today"):
                    out["uncared"] += 1
                if tile.get("fertilizer_available"):
                    out["manure"] += 1
                units = int(tile.get("yield_units", 0) or 0)
                if units > 0:
                    out["ripe_animal_units"] += units
            elif tile.get("kind") == "COOP":
                out["empty_coops"] += 1
            elif tile.get("kind") == "PASTURE":
                out["empty_pastures"] += 1
            elif tile.get("kind") == "PLANT":
                crop = str(tile.get("crop", ""))
                key = "crop_" + crop
                out[key] = out.get(key, 0) + 1
                if crop == "WHEAT":
                    out["wheat"] += 1
                if not tile.get("watered_today"):
                    out["dry"] += 1
                    out["unwatered_plants"] += 1
                units = int(tile.get("yield_units", 0) or 0)
                if units > 0:
                    out["ripe_crop_units"] += units
            elif tile.get("kind") == "WEED":
                pass
    return out


def _optimal_plant_day(crop, obs, day):
    """Return the earliest day we should plant this crop to align with demand."""
    if crop not in ("CARROT", "TOMATO"):
        return day  # plant immediately for wheat/others
    # Compute demand rate (units per step)
    rate = demand_rate(obs)
    rem = rate.get(crop, 0.0)
    book_depth = CROP_DEPTH.get(crop, 100)
    # If demand is strong (>70% of book depth per step), plant early; else delay a bit
    # We also consider the crop's first yield day: we want to start selling when
    # demand has already consumed some of the market to avoid early price depression.
    if rem / book_depth > 0.7:
        return min(day, 6)   # plant as soon as possible
    else:
        return min(day, 12)   # delay to let demand build and also enssure that the crop matures in time


def production_plan(obs, counts, day):
    """Decide what to plant and what animals to buy, using demand + denial."""
    demand = remaining_demand(obs)
    prices = obs.get("market", {}).get("prices", {})
    player = obs["player"]
    opponent_farm = obs["farms"][1 - player] if len(obs.get("farms", [])) > 1 else {}
    opp_counts = census(opponent_farm.get("tiles", [])) if opponent_farm else {}

    # Estimate opponent's future supply (simplified but robust)
    opp_units = {
        "MILK": opp_counts.get("cows", 0) * 15,
        "WOOL": opp_counts.get("sheep", 0) * 15,
        "EGG": opp_counts.get("geese", 0) * 25,
        "CARROT": opp_counts.get("crop_carrot", 0) * 4,
        "TOMATO": opp_counts.get("crop_tomato", 0) * 8,
        "STRAWBERRY": opp_counts.get("crop_strawberry", 0) * 8,
        "MELON": opp_counts.get("crop_melon", 0) * 6,
    }

    own_committed = {
        "CARROT": counts["crop_carrot"] * 4,
        "TOMATO": counts["crop_tomato"] * 8,
        "STRAWBERRY": counts["crop_strawberry"] * 8,
        "MELON": counts["crop_melon"] * 6,
        "EGG": counts["geese"] * 25,
        "MILK": counts["cows"] * 15,
        "WOOL": counts["sheep"] * 15,
    }

    plan = {
        "crop_targets": {},
        "animal_targets": {},
        "wheat_target": max(20, counts["animals"] * 2 + 5),
    }

    # ---- Crops ----
    crop_scores = []
    for crop in ["CARROT", "TOMATO", "STRAWBERRY", "MELON"]:
        # crop_can_mature(crop, planted_day, day): sowing today means
        # planted_day is today.
        if not crop_can_mature(crop, day, day):
            continue
        rem = demand.get(crop, 0.0)
        if rem <= 0:
            continue
        price = prices.get(crop, 0.0)
        if price < 1:
            continue
        # Marginal value of one more tile (≈4 units/tile)
        offset = opp_units.get(crop, 0) + own_committed.get(crop, 0)
        units_per_tile = 4 if crop in ["CARROT", "MELON"] else 6
        value = sale_revenue(obs, crop, units_per_tile, offset) / units_per_tile
        # Denial benefit
        opp_sales = opp_units.get(crop, 0)
        if opp_sales > 0:
            opp_loss = sale_revenue(obs, crop, opp_sales, 0) - sale_revenue(obs, crop, opp_sales, offset + units_per_tile)
            value += opp_loss / units_per_tile
        crop_scores.append((value, crop))

    crop_scores.sort(reverse=True)
    remaining_free = counts["free"]
    for val, crop in crop_scores:
        # Timing: only plant if day >= optimal_plant_day
        if day < _optimal_plant_day(crop, obs, day):
            continue
        max_tiles = min(
            20,
            int(demand.get(crop, 0) / 4),
            int(CROP_DEPTH.get(crop, 1000) / 4),
            remaining_free
        )
        if max_tiles <= 0:
            continue
        plan["crop_targets"][crop] = max_tiles
        remaining_free -= max_tiles

    # ---- Animals ----
    animal_scores = []
    for animal in ["GOOSE", "COW", "SHEEP"]:
        product = ANIMAL_PRODUCTS[animal]
        rem = demand.get(product, 0.0)
        if rem <= 0:
            continue
        price = prices.get(product, 0.0)
        if price < 1:
            continue
        if animal == "GOOSE":
            units_per_animal = 25 * 2
        elif animal == "COW":
            units_per_animal = 15 * 1.5
        else:
            units_per_animal = 15 * 1.0
        offset = opp_units.get(product, 0) + own_committed.get(product, 0)
        product_value = sale_revenue(obs, product, units_per_animal, offset)
        opp_sales = opp_units.get(product, 0)
        if opp_sales > 0:
            opp_loss = sale_revenue(obs, product, opp_sales, 0) - sale_revenue(obs, product, opp_sales, offset + units_per_animal)
            product_value += opp_loss
        manure_units = 25
        manure_price = prices.get("FERTILIZER", 0.0)
        if manure_price > 0:
            manure_value = manure_units * manure_price
            product_value += manure_value
        animal_scores.append((product_value - ANIMAL_COSTS[animal], animal))

    animal_scores.sort(reverse=True)
    # Choose top two animals; if one dominates, go heavier
    if len(animal_scores) >= 2 and animal_scores[0][0] > 1.5 * animal_scores[1][0]:
        best = animal_scores[0][1]
        plan["animal_targets"][best] = 18
        plan["animal_targets"][animal_scores[1][1]] = 2
    else:
        for _, animal in animal_scores[:2]:
            plan["animal_targets"][animal] = 9
    if "GOOSE" not in plan["animal_targets"]:
        plan["animal_targets"]["GOOSE"] = max(2, plan["animal_targets"].get("GOOSE", 0))

    return plan


def job_value(obs, tile, x, y, inventory, day, shed, seeds, counts, plan, closing):
    jobs = []
    player = obs["player"]
    farm = obs["farms"][player]
    board_size = len(farm["tiles"])
    egg_price = max(1.0, price_at("EGG", inventory_of(obs, "EGG")))
    initial_wheat_prices = [price_at("WHEAT", inventory_of(obs, "WHEAT"))]
    fert_price = max(1.0, price_at("FERTILIZER", inventory_of(obs, "FERTILIZER")))

    # ---- Shed ----
    if _shed_adjacent(x, y, board_size):
        if int(obs.get("step", 0)) >= 718:
            haul = 0.0
            for item, qty in inventory.items():
                if qty > 0 and item in MARKET_PARAMS:
                    haul += qty * price_at(item, inventory_of(obs, item))
            if haul > 0:
                jobs.append((6000.0 + haul, ["DROP"]))
        # Pickup wheat
        if counts["unfed"] > 0 and inventory.get("WHEAT", 0) <= 0:
            shed_wheat = shed.get("WHEAT", 0)
            if shed_wheat > 0:
                jobs.append((10000.0, ["PICKUP", "WHEAT", min(12, shed_wheat)]))
        # Pickup animals
        if not any(inventory.get(a, 0) > 0 for a in ANIMAL_PRODUCTS):
            for animal in ["GOOSE", "COW", "SHEEP"]:
                waiting = shed.get(animal, 0)
                if waiting <= 0:
                    continue
                home = ANIMAL_STRUCTURES[animal]
                free = counts["empty_coops"] if home == "COOP" else counts["empty_pastures"]
                if free <= 0:
                    continue
                carry = min(3, waiting, free)
                jobs.append((5000.0 - 100 * (animal != "GOOSE"), ["PICKUP", animal, carry]))
                break

    # ---- Empty tile ----
    if tile is None:
        # Plant wheat if needed
        if counts["wheat"] < plan["wheat_target"] and seeds.get("WHEAT", 0) > 0:
            if day <= LAST_DAY - 8:
                jobs.append((4000.0 + egg_price * 0.5, ["PLANT", "WHEAT"]))
        # Build pens
        for animal, target in plan["animal_targets"].items():
            home = ANIMAL_STRUCTURES[animal]
            current = counts["animals"] + shed.get(animal, 0)
            if current < target:
                if (home == "COOP" and counts["empty_coops"] < 6) or (home == "PASTURE" and counts["empty_pastures"] < 6):
                    build_action = ["BUILD_COOP"] if home == "COOP" else ["BUILD_PASTURE"]
                    jobs.append((3000.0, build_action))
                    break
        # Plant cash crops (timed)
        for crop, target in plan["crop_targets"].items():
            if counts.get("crop_" + crop, 0) < target and seeds.get(crop, 0) > 0:
                if day >= _optimal_plant_day(crop, obs, day) and day <= LAST_DAY - CROPS[crop]["first"] - 2:
                    price = price_at(crop, inventory_of(obs, crop))
                    jobs.append((2000.0 + price, ["PLANT", crop]))
                    break
        return jobs

    # ---- Existing tiles ----
    if not isinstance(tile, dict):
        return jobs

    kind = tile.get("kind")

    if "animal" in tile:
        animal = tile["animal"]
        units = int(tile.get("yield_units", 0) or 0)
        if not tile.get("fed_today") and inventory.get("WHEAT", 0) > 0:
            jobs.append((10000.0, ["FEED"]))
        if tile.get("fed_today") and not tile.get("cared_today"):
            jobs.append((8000.0, ["CARE"]))
        if tile.get("fertilizer_available"):
            jobs.append((3000.0 + fert_price, ["COLLECT_FERTILIZER"]))
        if units > 0 and (units >= 2 or closing):
            jobs.append((5000.0 + units * egg_price, ["HARVEST"]))

    elif kind in ("COOP", "PASTURE"):
        for animal, home in ANIMAL_STRUCTURES.items():
            if home == kind and inventory.get(animal, 0) > 0:
                jobs.append((4000.0, ["PLACE", animal]))
                break

    elif kind == "PLANT":
        crop = tile.get("crop", "")
        spec = CROPS.get(crop)
        if not spec:
            return jobs
        age = day - tile.get("planted_day", day)
        if not tile.get("watered_today"):
            jobs.append((2000.0 + egg_price * 0.3, ["WATER"]))
        if inventory.get("FERTILIZER", 0) > 0:
            gain = fertilizer_gain(tile, day)
            if gain > 0:
                worth = gain * price_at(crop, inventory_of(obs, crop))
                if worth > fert_price:
                    jobs.append((2500.0 + worth, ["FERTILIZE"]))
        units = int(tile.get("yield_units", 0) or 0)
        if units > 0 and age >= spec["first"]:
            urgent = age >= spec["max_day"] or units >= spec["max_yield"] or closing
            if urgent or not HARVEST_HOLD:
                jobs.append((3000.0 + units * price_at(crop, inventory_of(obs, crop)), ["HARVEST"]))

    elif kind == "WEED":
        jobs.append((500.0, ["DIG"]))

    return jobs


def candidate_hd_decide(obs: dict[str, Any]) -> AgentAction:
    farm = _farm(obs)
    tiles = farm.get("tiles", [])
    if not tiles:
        return {"farmer": PASS, "hands": [], "market": []}

    day = obs.get("day", 0)
    closing = day >= LAST_DAY - 1
    positions = _positions(farm)
    shed = _shed(obs)
    seeds = _seeds(obs)
    counts = census(tiles)
    money = farm.get("money", 0.0)

    # Production plan with timing
    plan = production_plan(obs, counts, day)

    # Worker assignment
    claimed = set()
    actions = []
    for worker, pos in enumerate(positions):
        inv = _inventory(obs, worker)
        best_score = -1e9
        best_action = PASS
        best_cell = None
        for y in range(len(tiles)):
            for x in range(len(tiles[y])):
                if (x, y) in claimed or not _owned(tiles, x, y):
                    continue
                tile = tiles[y][x]
                jobs = job_value(obs, tile, x, y, inv, day, shed, seeds, counts, plan, closing)
                travel = distance(pos, (x, y))
                for score, act in jobs:
                    final_score = score / ((travel + 1.0) ** TRAVEL_EXPONENT)
                    if act[0] in ("WATER", "FEED", "CARE"):
                        final_score *= 1.5
                    if final_score > best_score:
                        best_score = final_score
                        best_cell = (x, y)
                        best_action = step_toward(pos, (x, y), act) if travel > 0 else act
        if best_cell is not None:
            claimed.add(best_cell)
            actions.append(best_action)
        else:
            actions.append(PASS)

    # Market orders
    market = []
    # Sell paced
    for item in ["EGG", "FERTILIZER", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "WHEAT", "MILK", "WOOL"]:
        held = shed.get(item, 0)
        if held <= 0:
            continue
        if item == "WHEAT":
            reserve = counts["animals"] * 2
            if held <= reserve:
                continue
            held -= reserve
        demand = remaining_demand(obs).get(item, 0.0)
        max_sell = max(1, int(demand * SELL_PACE)) if demand > 0 else 10
        sell_qty = min(held, max_sell)
        if sell_qty > 0:
            market.append(["SELL", item, sell_qty])

    # Wheat seed. The original had a wheat_target and a PLANT WHEAT job but
    # no order to buy the seed, so wheat could never be sown, the animals
    # were never fed, and with no produce there was no income -- the farm
    # sat at nought coins from day zero. Bought before hiring, because the
    # crew is worthless without something to work on.
    if seeds.get("WHEAT", 0) < 10 and money > EMERGENCY_FLOOR:
        market.append(["BUY_SEED", "WHEAT", 10 - int(seeds.get("WHEAT", 0))])

    # Hire hands
    hands = len(farm.get("hands", []))
    # Ramp the crew instead of hiring eleven on day zero: the wage is
    # fibonacci in the number hired that day, and the original spent its
    # whole purse on hands before it owned a single seed.
    target_hands = min(HAND_CAP, 4 + day)
    if hands < target_hands and day <= 27 and obs.get("hour", 0) <= 2:
        for _ in range(min(4, target_hands - hands)):
            market.append(["HIRE"])

    # Buy land
    # `day == OPENING_LAND_DAY` is true for all twenty-four turns of that
    # day, and `quadrants` only updates once a purchase resolves, so the
    # original issued BUY_LAND two dozen times over and spent the purse on
    # ground it could not work. One order, one turn, behind a reserve.
    quadrants = len(farm.get("unlocked_quadrants", []))
    hour = int(obs.get("hour", 0))
    if quadrants < MAX_QUADRANTS and day == OPENING_LAND_DAY and hour == 1:
        if money > 1200:
            market.append(["BUY_LAND"])
    elif quadrants == 2 and day >= 9 and hour == 1 and money > 2000:
        market.append(["BUY_LAND"])

    # Buy seeds
    for crop, target in plan["crop_targets"].items():
        current = counts.get("crop_" + crop, 0)
        if current < target and seeds.get(crop, 0) < 10:
            need = target - current
            want = min(need, 10)
            if money > 300:
                market.append(["BUY_SEED", crop, want])

    # Buy animals
    # census counts geese/cows/sheep; "gooses" and "sheeps" are not keys, so
    # the original read zero for two of the three and bought without end.
    census_key = {"GOOSE": "geese", "COW": "cows", "SHEEP": "sheep"}
    for animal, target in plan["animal_targets"].items():
        current = (counts.get(census_key[animal], 0)
                   + shed.get(animal, 0))
        if current < target:
            home = ANIMAL_STRUCTURES[animal]
            free = counts["empty_coops"] if home == "COOP" else counts["empty_pastures"]
            if free > 0 and money > ANIMAL_COSTS[animal] + EMERGENCY_FLOOR:
                want = min(target - current, free)
                market.append(["BUY_ANIMAL", animal, want])

    # Emergency feed
    if counts["unfed"] > 0 and shed.get("WHEAT", 0) <= 0 and money > EMERGENCY_FLOOR:
        market.append(["BUY_PRODUCT", "WHEAT", min(counts["unfed"], 6)])

    market = market[:10]

    return {
        "farmer": actions[0] if actions else PASS,
        "hands": actions[1:] if len(actions) > 1 else [],
        "market": market,
    }


def agent(obs):
    return candidate_hd_decide(obs)