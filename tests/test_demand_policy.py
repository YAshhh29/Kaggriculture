import unittest

from policies.demand_policy import (
    expansion_animal_plans,
    select_expansion_animal,
    select_rotation_crop,
)
from tests.test_experimental_scale_agent import scale_observation


class DemandPolicyTests(unittest.TestCase):
    def test_pet_cafe_selects_carrot_rotation(self) -> None:
        state = scale_observation(day=9)
        state["town"]["unlocked_shops"] = ["PET_CAFE"]

        self.assertEqual(select_rotation_crop(state), "CARROT")

    def test_smoothie_demand_can_select_strawberry_rotation(self) -> None:
        state = scale_observation(day=9)
        state["town"]["unlocked_shops"] = [
            "SMOOTHIE_SHOP",
            "SMOOTHIE_SHOP",
        ]

        self.assertEqual(select_rotation_crop(state), "STRAWBERRY")

    def test_bakery_selects_goose_for_two_expansion_slots(self) -> None:
        state = scale_observation(day=4)
        state["town"]["unlocked_shops"] = ["BAKERY"]
        animal = select_expansion_animal(state)
        plans = expansion_animal_plans(animal)

        self.assertEqual(animal, "GOOSE")
        self.assertEqual(
            sum(plan["animal"] == "GOOSE" for plan in plans),
            2,
        )

    def test_no_specialist_animal_demand_keeps_balanced_plan(self) -> None:
        state = scale_observation(day=4)

        self.assertEqual(select_expansion_animal(state), "SHEEP")


if __name__ == "__main__":
    unittest.main()
