import unittest
from unittest.mock import patch

from agents.experimental_guarded_carried_crop_service_agent import decide
from tests.test_experimental_scale_agent import scale_observation


class ExperimentalGuardedCarriedCropServiceAgentTests(unittest.TestCase):
    def test_forwards_bounded_carried_service_when_selected(self) -> None:
        state = scale_observation(day=6)
        with (
            patch(
                "agents.experimental_guarded_carried_crop_service_agent."
                "_choices",
                return_value=("COW", "WHEAT"),
            ),
            patch(
                "agents.experimental_guarded_carried_crop_service_agent."
                "_crop_service_selected",
                return_value=True,
            ),
            patch(
                "agents.experimental_guarded_carried_crop_service_agent."
                "_selected_hand_targets",
                return_value=tuple([12] * 30),
            ),
            patch(
                "agents.experimental_guarded_carried_crop_service_agent."
                "decide_demand",
                return_value={"farmer": ["PASS"], "hands": [], "market": []},
            ) as demand,
        ):
            decide(state)

        self.assertTrue(demand.call_args.kwargs["fertilize_strawberries"])
        self.assertEqual(
            demand.call_args.kwargs[
                "fertilized_strawberries_per_quadrant"
            ],
            1,
        )
        self.assertTrue(demand.call_args.kwargs["carried_fertilizer_only"])
        self.assertTrue(
            demand.call_args.kwargs["pair_colocated_strawberry_service"]
        )


if __name__ == "__main__":
    unittest.main()