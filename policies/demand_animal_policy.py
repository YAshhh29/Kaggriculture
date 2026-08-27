"""Safe day-6 expansion-animal arms for contextual learning."""

from __future__ import annotations

from collections import Counter
from typing import Any

from agents.experimental_deadline_tapered_wheat_agent import DEADLINE_HAND_TARGETS
from agents.experimental_learned_service_agent import _selected_arm
from agents.experimental_premium_throughput_agent import decide as decide_premium
from core.economics import animal_opportunity
from policies.demand_policy import expansion_animal_plans
from policies.macro_policy import FEATURE_NAMES, extract_macro_features
from policies.service_policy import ARM_PAIRED


ARM_BALANCED = 0
ARM_COW = 1
ARM_GOOSE = 2
DEMAND_ANIMAL_ARMS = (ARM_BALANCED, ARM_COW, ARM_GOOSE)
ARM_NAMES = {
    ARM_BALANCED: "balanced-sheep",
    ARM_COW: "milk-demand-cows",
    ARM_GOOSE: "egg-demand-geese",
}
ARM_ANIMALS = {
    ARM_BALANCED: "SHEEP",
    ARM_COW: "COW",
    ARM_GOOSE: "GOOSE",
}
EGG_SHOPS = {"BAKERY", "BRUNCH_SPOT"}
CARROT_SHOPS = {"PET_CAFE", "FARMERS_MARKET"}
TOMATO_SHOPS = {"PIZZA_SHOP", "FARMERS_MARKET"}
DEMAND_ANIMAL_FEATURE_NAMES = (
    *FEATURE_NAMES,
    "shops_egg",
    "shops_carrot",
    "shops_tomato",
    "opportunity_goose",
    "opportunity_cow",
    "opportunity_sheep",
)


def extract_demand_animal_features(
    observation: dict[str, Any],
) -> dict[str, float]:
    """Extend stable macro features with demand-animal opportunity signals."""
    features = extract_macro_features(observation)
    shops = Counter(observation.get("town", {}).get("unlocked_shops", []))
    features.update(
        {
            "shops_egg": float(sum(shops[shop] for shop in EGG_SHOPS)),
            "shops_carrot": float(
                sum(shops[shop] for shop in CARROT_SHOPS)
            ),
            "shops_tomato": float(
                sum(shops[shop] for shop in TOMATO_SHOPS)
            ),
            "opportunity_goose": animal_opportunity(
                observation, "GOOSE"
            ).score,
            "opportunity_cow": animal_opportunity(
                observation, "COW"
            ).score,
            "opportunity_sheep": animal_opportunity(
                observation, "SHEEP"
            ).score,
        }
    )
    return {
        name: features[name] for name in DEMAND_ANIMAL_FEATURE_NAMES
    }


def decide_demand_animal_arm(
    observation: dict[str, Any],
    arm: int,
) -> dict[str, Any]:
    """Execute one expansion-animal arm through deterministic safety."""
    if arm not in DEMAND_ANIMAL_ARMS:
        raise ValueError(f"Unknown demand-animal arm: {arm}")
    service_arm = _selected_arm(observation)
    return decide_premium(
        observation,
        target_extra_land=2,
        animal_plans=expansion_animal_plans(ARM_ANIMALS[arm]),
        rotation_crop="WHEAT",
        land_reserves=(300, 300),
        late_rotation_crop="WHEAT",
        release_idle_crop_reserve=True,
        prioritize_mature_harvest=True,
        hand_targets=DEADLINE_HAND_TARGETS,
        pair_colocated_feed_care=service_arm == ARM_PAIRED,
    )
