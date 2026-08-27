import unittest
from unittest.mock import patch

from agents.experimental_demand_aware_agent import (
    _ANIMAL_CHOICES,
    _CROP_CHOICES,
    _choices,
    decide,
    decide_demand,
)
from policies.service_policy import ARM_PAIRED
from tests.test_experimental_scale_agent import scale_observation


class ExperimentalDemandAwareAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        _ANIMAL_CHOICES.clear()
        _CROP_CHOICES.clear()

    def test_choices_lock_after_selection_days(self) -> None:
        state = scale_observation(day=9)
        state["town"]["unlocked_shops"] = ["PET_CAFE"]

        first = _choices(state)
        state["town"]["unlocked_shops"] = ["BAKERY"]
        second = _choices(state)

        self.assertEqual(first, second)

    def test_decide_combines_demand_and_service_choices(self) -> None:
        state = scale_observation(day=9)
        _ANIMAL_CHOICES[0] = "GOOSE"
        _CROP_CHOICES[0] = "CARROT"
        with (
            patch(
                "agents.experimental_demand_aware_agent._selected_arm",
                return_value=ARM_PAIRED,
            ),
            patch(
                "agents.experimental_demand_aware_agent.decide_premium"
            ) as premium,
        ):
            decide(state)

        self.assertEqual(premium.call_args.kwargs["rotation_crop"], "CARROT")
        self.assertTrue(
            premium.call_args.kwargs["pair_colocated_feed_care"]
        )
        self.assertEqual(
            sum(
                plan["animal"] == "GOOSE"
                for plan in premium.call_args.kwargs["animal_plans"]
            ),
            2,
        )

    def test_each_demand_axis_can_be_disabled(self) -> None:
        state = scale_observation(day=9)
        _ANIMAL_CHOICES[0] = "GOOSE"
        _CROP_CHOICES[0] = "CARROT"
        with (
            patch(
                "agents.experimental_demand_aware_agent._selected_arm",
                return_value=ARM_PAIRED,
            ),
            patch(
                "agents.experimental_demand_aware_agent.decide_premium"
            ) as premium,
        ):
            decide_demand(
                state,
                use_crop_demand=False,
                use_animal_demand=False,
            )

        self.assertEqual(premium.call_args.kwargs["rotation_crop"], "WHEAT")
        self.assertEqual(
            sum(
                plan["animal"] == "GOOSE"
                for plan in premium.call_args.kwargs["animal_plans"]
            ),
            0,
        )

    def test_unsupported_opening_falls_back_to_balanced_animals(self) -> None:
        state = scale_observation(day=6)
        state["farms"][1]["money"] = 177
        state["town"]["unlocked_shops"] = [
            "SMOOTHIE_SHOP",
            "ICE_CREAM_SHOP",
        ]

        animal, _ = _choices(state)

        self.assertEqual(animal, "SHEEP")


if __name__ == "__main__":
    unittest.main()
