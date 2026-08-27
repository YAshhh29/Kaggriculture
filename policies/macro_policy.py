"""Public observation features and inference for learned macro policies."""

from __future__ import annotations

from collections import Counter
from math import sqrt
from typing import Any


ARM_COMPACT = 0
ARM_EXPANDED = 1
ARM_COMPACT_CROP = 2
ARM_EXPANDED_CROP = 3
MACRO_ARMS = (
    ARM_COMPACT,
    ARM_EXPANDED,
    ARM_COMPACT_CROP,
    ARM_EXPANDED_CROP,
)
FEATURE_NAMES = (
    "player",
    "own_money_k",
    "opponent_money_k",
    "money_lead_k",
    "opponent_hands",
    "opponent_land",
    "opponent_wheat",
    "opponent_nonwheat",
    "opponent_cows",
    "opponent_sheep",
    "opponent_geese",
    "opponent_structures",
    "opponent_weeds",
    "price_wheat",
    "price_strawberry",
    "price_melon",
    "price_milk",
    "price_wool",
    "price_fertilizer",
    "shops_wheat",
    "shops_strawberry",
    "shops_milk",
    "shops_wool",
)
WHEAT_SHOPS = {
    "BAKERY",
    "BRUNCH_SPOT",
    "FARMERS_MARKET",
    "ICE_CREAM_SHOP",
    "PIZZA_SHOP",
}
STRAWBERRY_SHOPS = {
    "BRUNCH_SPOT",
    "FARMERS_MARKET",
    "ICE_CREAM_SHOP",
    "SMOOTHIE_SHOP",
}
MILK_SHOPS = {"ICE_CREAM_SHOP", "PIZZA_SHOP", "SMOOTHIE_SHOP"}


def _public_counts(farm: dict[str, Any]) -> dict[str, Counter[str]]:
    counts = {
        "crops": Counter(),
        "animals": Counter(),
        "structures": Counter(),
        "terrain": Counter(),
    }
    for row in farm.get("tiles", []):
        for tile in row:
            if not isinstance(tile, dict):
                continue
            if tile.get("kind") == "PLANT":
                counts["crops"][str(tile.get("crop", "UNKNOWN"))] += 1
            if tile.get("animal"):
                counts["animals"][str(tile["animal"])] += 1
            if tile.get("kind") in {"COOP", "PASTURE"}:
                counts["structures"][str(tile["kind"])] += 1
            if tile.get("kind") == "WEED":
                counts["terrain"]["WEED"] += 1
    return counts


def extract_macro_features(observation: dict[str, Any]) -> dict[str, float]:
    """Extract only state that is public to both players."""
    player = int(observation["player"])
    farms = observation["farms"]
    own = farms[player]
    opponent = farms[1 - player]
    counts = _public_counts(opponent)
    crops = counts["crops"]
    animals = counts["animals"]
    prices = observation.get("market", {}).get("prices", {})
    shops = Counter(observation.get("town", {}).get("unlocked_shops", []))
    own_money = float(own.get("money", 0))
    opponent_money = float(opponent.get("money", 0))

    features = {
        "player": float(player),
        "own_money_k": own_money / 1000.0,
        "opponent_money_k": opponent_money / 1000.0,
        "money_lead_k": (own_money - opponent_money) / 1000.0,
        "opponent_hands": float(len(opponent.get("hands", []))),
        "opponent_land": float(len(opponent.get("unlocked_quadrants", []))),
        "opponent_wheat": float(crops["WHEAT"]),
        "opponent_nonwheat": float(sum(crops.values()) - crops["WHEAT"]),
        "opponent_cows": float(animals["COW"]),
        "opponent_sheep": float(animals["SHEEP"]),
        "opponent_geese": float(animals["GOOSE"]),
        "opponent_structures": float(sum(counts["structures"].values())),
        "opponent_weeds": float(counts["terrain"]["WEED"]),
        "price_wheat": float(prices.get("WHEAT", 0)) / 25.0,
        "price_strawberry": float(prices.get("STRAWBERRY", 0)) / 120.0,
        "price_melon": float(prices.get("MELON", 0)) / 250.0,
        "price_milk": float(prices.get("MILK", 0)) / 160.0,
        "price_wool": float(prices.get("WOOL", 0)) / 200.0,
        "price_fertilizer": float(prices.get("FERTILIZER", 0)) / 100.0,
        "shops_wheat": float(sum(shops[shop] for shop in WHEAT_SHOPS)),
        "shops_strawberry": float(
            sum(shops[shop] for shop in STRAWBERRY_SHOPS)
        ),
        "shops_milk": float(sum(shops[shop] for shop in MILK_SHOPS)),
        "shops_wool": float(shops["YARN_STORE"]),
    }
    return {name: features[name] for name in FEATURE_NAMES}


def select_macro_arm(
    model: dict[str, Any],
    features: dict[str, float],
) -> int:
    """Evaluate a learned macro policy."""
    if model.get("type") == "knn":
        return _select_knn_arm(model, features)
    node = model
    while "arm" not in node:
        feature = str(node["feature"])
        branch = (
            "left"
            if features[feature] <= float(node["threshold"])
            else "right"
        )
        node = node[branch]
    arm = int(node["arm"])
    if arm not in MACRO_ARMS:
        raise ValueError(f"Unknown macro arm: {arm}")
    return arm


def _select_knn_arm(
    model: dict[str, Any],
    features: dict[str, float],
) -> int:
    names = [str(name) for name in model["features"]]
    means = model["means"]
    scales = model["scales"]
    distances = []
    for example in model["examples"]:
        squared = sum(
            (
                (features[name] - float(example["features"][name]))
                / float(scales[name])
            ) ** 2
            for name in names
        )
        distances.append((sqrt(squared), example))
    neighbors = sorted(distances, key=lambda item: item[0])[
        : int(model["k"])
    ]
    power = float(model.get("distance_power", 1.0))
    scores = {}
    for arm in MACRO_ARMS:
        weighted = 0.0
        weight_sum = 0.0
        for distance, example in neighbors:
            if str(arm) not in example["outcomes"]:
                continue
            weight = 1.0 if power == 0 else 1.0 / (distance + 0.1) ** power
            weighted += weight * float(
                example["outcomes"][str(arm)]["utility"]
            )
            weight_sum += weight
        if weight_sum > 0:
            scores[arm] = weighted / weight_sum
    if not scores:
        raise ValueError("KNN macro model has no compatible arm outcomes")
    return max(scores, key=lambda arm: (scores[arm], arm))
