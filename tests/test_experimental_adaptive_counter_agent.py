import copy
import unittest

from agents.experimental_adaptive_counter_agent import (
    ONE_LAND_ANIMAL_PLANS,
    _is_wheat_specialist,
    _strategy_parameters,
    decide as decide_adaptive,
)
from agents.experimental_premium_throughput_agent import decide as decide_premium
from tests.test_experimental_scale_agent import scale_observation


def _opponent_crop_state(*, crop: str, count: int, day: int = 9) -> dict:
    state = scale_observation(day=day)
    state["farms"][1] = copy.deepcopy(state["farms"][0])
    for index in range(count):
        x, y = index % 5, index // 5
        state["farms"][1]["tiles"][y][x] = {
            "kind": "PLANT",
            "crop": crop,
            "planted_day": 0,
        }
    return state


class ExperimentalAdaptiveCounterAgentTests(unittest.TestCase):
    def test_detects_only_established_all_wheat_opponents(self) -> None:
        wheat = _opponent_crop_state(crop="WHEAT", count=5)
        diversified = copy.deepcopy(wheat)
        diversified["farms"][1]["tiles"][0][0]["crop"] = "STRAWBERRY"
        early = _opponent_crop_state(crop="WHEAT", count=5, day=3)
        empty = _opponent_crop_state(crop="WHEAT", count=0)

        self.assertTrue(_is_wheat_specialist(wheat))
        self.assertTrue(_is_wheat_specialist(empty))
        self.assertFalse(_is_wheat_specialist(diversified))
        self.assertFalse(_is_wheat_specialist(early))

    def test_wheat_specialist_uses_one_land(self) -> None:
        state = _opponent_crop_state(crop="WHEAT", count=5)

        target_land, animal_plans, rotation_crop = _strategy_parameters(state)

        self.assertEqual(target_land, 1)
        self.assertEqual(len(animal_plans), 8)
        self.assertEqual(rotation_crop, "STRAWBERRY")

    def test_diversified_opponent_keeps_two_land_plan(self) -> None:
        state = _opponent_crop_state(crop="STRAWBERRY", count=5)

        target_land, animal_plans, rotation_crop = _strategy_parameters(state)

        self.assertEqual(target_land, 2)
        self.assertEqual(len(animal_plans), 12)
        self.assertEqual(rotation_crop, "STRAWBERRY")

    def test_wheat_branch_matches_validated_one_land_policy(self) -> None:
        state = _opponent_crop_state(crop="WHEAT", count=5)

        self.assertEqual(
            decide_adaptive(state),
            decide_premium(
                state,
                target_extra_land=1,
                animal_plans=ONE_LAND_ANIMAL_PLANS,
            ),
        )

    def test_diversified_branch_matches_validated_two_land_policy(
        self,
    ) -> None:
        state = _opponent_crop_state(crop="STRAWBERRY", count=5)

        self.assertEqual(decide_adaptive(state), decide_premium(state))


if __name__ == "__main__":
    unittest.main()
