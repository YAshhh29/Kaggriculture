"""Decision-time workload features for live macro selection."""

from __future__ import annotations

from typing import Any

from policies.macro_policy import FEATURE_NAMES, extract_macro_features


LIVE_FEATURE_NAMES = FEATURE_NAMES + (
    "own_hands",
    "own_land",
    "own_wheat",
    "own_nonwheat",
    "own_strawberries",
    "own_unwatered_crops",
    "own_stressed_crops",
    "own_harvestable_crop_units",
    "own_animals",
    "own_cows",
    "own_sheep",
    "own_geese",
    "own_due_feed",
    "own_due_care",
    "own_collectable_animal_units",
    "own_fertilizer_stock",
    "own_service_tasks_per_worker",
)


def extract_live_macro_features(
    observation: dict[str, Any],
) -> dict[str, float]:
    """Add own service burden to the public opponent and market context."""
    features = extract_macro_features(observation)
    player = int(observation["player"])
    farm = observation["farms"][player]
    private = observation.get("private", {})
    crops = []
    animals = []
    for row in farm.get("tiles", []):
        for tile in row:
            if not isinstance(tile, dict):
                continue
            if tile.get("kind") == "PLANT":
                crops.append(tile)
            if tile.get("animal"):
                animals.append(tile)

    unwatered = sum(not tile.get("watered_today", False) for tile in crops)
    harvestable_crops = sum(
        int(tile.get("yield_units", 0)) for tile in crops
    )
    due_feed = sum(
        not tile.get("fed_today", False)
        and int(tile.get("consecutive_unfed", 0)) >= 1
        for tile in animals
    )
    due_care = sum(
        tile.get("fed_today", False)
        and not tile.get("cared_today", False)
        for tile in animals
    )
    collectable_animals = sum(
        int(tile.get("yield_units", 0)) for tile in animals
    )
    service_tasks = (
        unwatered
        + sum(int(tile.get("yield_units", 0)) > 0 for tile in crops)
        + due_feed
        + due_care
        + sum(int(tile.get("yield_units", 0)) > 0 for tile in animals)
    )
    workers = 1 + len(farm.get("hands", []))
    inventories = private.get("inventories", [])
    fertilizer_stock = int(
        private.get("shed", {}).get("FERTILIZER", 0)
    ) + sum(
        int(inventory.get("FERTILIZER", 0))
        for inventory in inventories
        if isinstance(inventory, dict)
    )
    own_features = {
        "own_hands": float(len(farm.get("hands", []))),
        "own_land": float(len(farm.get("unlocked_quadrants", []))),
        "own_wheat": float(sum(tile.get("crop") == "WHEAT" for tile in crops)),
        "own_nonwheat": float(sum(tile.get("crop") != "WHEAT" for tile in crops)),
        "own_strawberries": float(
            sum(tile.get("crop") == "STRAWBERRY" for tile in crops)
        ),
        "own_unwatered_crops": float(unwatered),
        "own_stressed_crops": float(
            sum(int(tile.get("consecutive_unwatered", 0)) > 0 for tile in crops)
        ),
        "own_harvestable_crop_units": float(harvestable_crops),
        "own_animals": float(len(animals)),
        "own_cows": float(sum(tile.get("animal") == "COW" for tile in animals)),
        "own_sheep": float(
            sum(tile.get("animal") == "SHEEP" for tile in animals)
        ),
        "own_geese": float(
            sum(tile.get("animal") == "GOOSE" for tile in animals)
        ),
        "own_due_feed": float(due_feed),
        "own_due_care": float(due_care),
        "own_collectable_animal_units": float(collectable_animals),
        "own_fertilizer_stock": float(fertilizer_stock),
        "own_service_tasks_per_worker": service_tasks / workers,
    }
    return {name: (features | own_features)[name] for name in LIVE_FEATURE_NAMES}