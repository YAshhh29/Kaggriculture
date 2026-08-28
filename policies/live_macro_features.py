"""Decision-time workload features for live macro selection."""

from __future__ import annotations

from typing import Any

from core.routing import distance
from policies.macro_policy import FEATURE_NAMES, extract_macro_features


PREMIUM_SERVICE_AGES = {
    "MELON": frozenset({6, 7, 8, 9, 10}),
    "STRAWBERRY": frozenset({9, 11, 13, 15}),
}


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
    "own_fertilizer_carriers",
    "own_carried_fertilizer",
    "own_due_melons",
    "own_due_strawberries",
    "own_unfertilized_due_melons",
    "own_unfertilized_due_strawberries",
    "own_unfertilized_due_premium",
    "own_workers_on_due_melons",
    "own_workers_on_due_strawberries",
    "own_workers_on_due_premium",
    "own_min_carrier_distance_to_due_melons",
    "own_min_carrier_distance_to_due_strawberries",
    "own_min_carrier_distance_to_due_premium",
    "own_mean_worker_distance_to_due_premium",
    "own_pending_feed",
    "own_pending_care",
    "own_pending_animal_harvests",
    "own_pending_fertilizer_collection",
    "own_pending_animal_service_per_worker",
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
    positions = [
        tuple(farm.get("farmer", (0, 0))),
        *(tuple(position) for position in farm.get("hands", [])),
    ]
    carried_fertilizer = [
        int(inventory.get("FERTILIZER", 0))
        if isinstance(inventory, dict) else 0
        for inventory in inventories[:len(positions)]
    ]
    carriers = [
        worker
        for worker, quantity in enumerate(carried_fertilizer)
        if quantity > 0
    ]
    day = int(observation.get("day", 0))
    due_by_crop: dict[str, list[tuple[int, int]]] = {
        "MELON": [],
        "STRAWBERRY": [],
    }
    unfertilized_by_crop = {"MELON": 0, "STRAWBERRY": 0}
    for y, row in enumerate(farm.get("tiles", [])):
        for x, tile in enumerate(row):
            if not isinstance(tile, dict):
                continue
            crop = str(tile.get("crop", ""))
            if crop not in PREMIUM_SERVICE_AGES:
                continue
            age = day - int(tile.get("planted_day", day))
            if (
                age not in PREMIUM_SERVICE_AGES[crop]
                or tile.get("watered_today", False)
            ):
                continue
            due_by_crop[crop].append((x, y))
            unfertilized_by_crop[crop] += (
                int(tile.get("fertilized_until_day", -1)) < day
            )
    due_premium = [
        target
        for crop in PREMIUM_SERVICE_AGES
        for target in due_by_crop[crop]
    ]
    board_diameter = max(1, 2 * (len(farm.get("tiles", [])) - 1))
    no_target_distance = float(board_diameter + 1)
    carrier_distances = [
        distance(positions[worker], target)
        for worker in carriers
        for target in due_premium
    ]
    minimum_carrier_distance_by_crop = {
        crop: float(
            min(
                (
                    distance(positions[worker], target)
                    for worker in carriers
                    for target in targets
                ),
                default=no_target_distance,
            )
        )
        for crop, targets in due_by_crop.items()
    }
    worker_target_distances = [
        min(distance(position, target) for position in positions)
        for target in due_premium
    ] if positions else []
    pending_feed = sum(
        not tile.get("fed_today", False) for tile in animals
    )
    pending_care = sum(
        not tile.get("cared_today", False) for tile in animals
    )
    pending_animal_harvests = sum(
        int(tile.get("yield_units", 0)) > 0 for tile in animals
    )
    pending_fertilizer_collection = sum(
        tile.get("fertilizer_available", False) for tile in animals
    )
    pending_animal_service = (
        pending_feed
        + pending_care
        + pending_animal_harvests
        + pending_fertilizer_collection
    )
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
        "own_nonwheat": float(
            sum(tile.get("crop") != "WHEAT" for tile in crops)
        ),
        "own_strawberries": float(
            sum(tile.get("crop") == "STRAWBERRY" for tile in crops)
        ),
        "own_unwatered_crops": float(unwatered),
        "own_stressed_crops": float(
            sum(
                int(tile.get("consecutive_unwatered", 0)) > 0
                for tile in crops
            )
        ),
        "own_harvestable_crop_units": float(harvestable_crops),
        "own_animals": float(len(animals)),
        "own_cows": float(
            sum(tile.get("animal") == "COW" for tile in animals)
        ),
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
        "own_fertilizer_carriers": float(len(carriers)),
        "own_carried_fertilizer": float(sum(carried_fertilizer)),
        "own_due_melons": float(len(due_by_crop["MELON"])),
        "own_due_strawberries": float(len(due_by_crop["STRAWBERRY"])),
        "own_unfertilized_due_melons": float(
            unfertilized_by_crop["MELON"]
        ),
        "own_unfertilized_due_strawberries": float(
            unfertilized_by_crop["STRAWBERRY"]
        ),
        "own_unfertilized_due_premium": float(
            sum(unfertilized_by_crop.values())
        ),
        "own_workers_on_due_melons": float(
            sum(position in due_by_crop["MELON"] for position in positions)
        ),
        "own_workers_on_due_strawberries": float(
            sum(
                position in due_by_crop["STRAWBERRY"]
                for position in positions
            )
        ),
        "own_workers_on_due_premium": float(
            sum(position in due_premium for position in positions)
        ),
        "own_min_carrier_distance_to_due_melons": (
            minimum_carrier_distance_by_crop["MELON"]
        ),
        "own_min_carrier_distance_to_due_strawberries": (
            minimum_carrier_distance_by_crop["STRAWBERRY"]
        ),
        "own_min_carrier_distance_to_due_premium": float(
            min(carrier_distances, default=no_target_distance)
        ),
        "own_mean_worker_distance_to_due_premium": (
            sum(worker_target_distances) / len(worker_target_distances)
            if worker_target_distances else no_target_distance
        ),
        "own_pending_feed": float(pending_feed),
        "own_pending_care": float(pending_care),
        "own_pending_animal_harvests": float(pending_animal_harvests),
        "own_pending_fertilizer_collection": float(
            pending_fertilizer_collection
        ),
        "own_pending_animal_service_per_worker": (
            pending_animal_service / workers
        ),
    }
    combined = features | own_features
    return {name: combined[name] for name in LIVE_FEATURE_NAMES}
