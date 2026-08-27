import unittest
from unittest.mock import patch

from agents.experimental_colocated_crop_service_agent import decide
from tests.test_experimental_scale_agent import scale_observation


class ExperimentalColocatedCropServiceAgentTests(unittest.TestCase):
    def test_enables_only_colocated_crop_service_axis(self) -> None:
        state = scale_observation(day=9)
        with (
            patch(
                "agents.experimental_colocated_crop_service_agent._choices",
                return_value=("SHEEP", "WHEAT"),
            ),
            patch(
                "agents.experimental_colocated_crop_service_agent.decide_demand"
            ) as demand,
        ):
            decide(state)

        self.assertTrue(
            demand.call_args.kwargs["pair_colocated_strawberry_service"]
        )
        self.assertFalse(demand.call_args.kwargs["use_crop_demand"])


if __name__ == "__main__":
    unittest.main()